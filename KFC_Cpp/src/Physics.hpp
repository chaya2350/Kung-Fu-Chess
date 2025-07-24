#pragma once

#include "Board.hpp"
#include "Command.hpp"
#include "Common.hpp"
#include <optional>
#include <cmath>

class BasePhysics {
public:
    explicit BasePhysics(const Board& board, double param = 1.0)
        : board(board), param(param) {}

    virtual ~BasePhysics() = default;

    virtual void reset(const Command& cmd) = 0;
    virtual std::optional<Command> update(int now_ms) = 0;

    std::pair<float,float> get_pos_m() const { return curr_pos_m; }
    std::pair<int,int> get_pos_pix() const { return board.m_to_pix(curr_pos_m); }
    std::pair<int,int> get_curr_cell() const { return board.m_to_cell(curr_pos_m); }

    int get_start_ms() const { return start_ms; }

    virtual bool can_be_captured() const { return true; }
    virtual bool can_capture() const { return true; }
    virtual bool is_movement_blocker() const { return false; }

protected:
    const Board& board;
    double param{1.0};

    std::pair<int,int> start_cell;
    std::pair<int,int> end_cell;
    std::pair<float,float> curr_pos_m{0,0};
    int start_ms{0};
};

// ---------------------------------------------------------------------------
class IdlePhysics : public BasePhysics {
public:
    using BasePhysics::BasePhysics;
    void reset(const Command& cmd) override {
        if(cmd.type == "done") {
            if(start_cell == std::pair<int,int>{0,0})
                start_cell = {0,0};
            end_cell = start_cell;
        } else if(cmd.params.empty()) {
            start_cell = end_cell = {0,0};
        } else {
            start_cell = end_cell = cmd.params[0];
        }
        curr_pos_m = board.cell_to_m(start_cell);
        start_ms = cmd.timestamp;
    }
    std::optional<Command> update(int) override { return std::nullopt; }

    bool can_capture() const override { return false; }
    bool is_movement_blocker() const override { return true; }
};

// ---------------------------------------------------------------------------
class MovePhysics : public BasePhysics {
public:
    explicit MovePhysics(const Board& board, double speed_cells_per_s)
        : BasePhysics(board, speed_cells_per_s) {}

    void reset(const Command& cmd) override {
        start_cell = cmd.params[0];
        end_cell   = cmd.params[1];
        curr_pos_m = board.cell_to_m(start_cell);
        start_ms   = cmd.timestamp;

        std::pair<float,float> start_pos = board.cell_to_m(start_cell);
        std::pair<float,float> end_pos   = board.cell_to_m(end_cell);
        movement_vec = { end_pos.first - start_pos.first, end_pos.second - start_pos.second };
        movement_len = std::hypot(movement_vec.first, movement_vec.second);
        double speed_m_s = param; // 1 cell == 1m with default cell_size_m
        duration_s = movement_len / speed_m_s;
    }

    std::optional<Command> update(int now_ms) override {
        double seconds = (now_ms - start_ms) / 1000.0;
        if(seconds >= duration_s) {
            curr_pos_m = board.cell_to_m(end_cell);
            return std::optional<Command>{Command{now_ms, "", "done", {}}};
        }
        double ratio = seconds / duration_s;
        curr_pos_m = { board.cell_to_m(start_cell).first + movement_vec.first * ratio,
                       board.cell_to_m(start_cell).second + movement_vec.second * ratio };
        return std::nullopt;
    }

private:
    std::pair<float,float> movement_vec{0,0};
    double movement_len{0};
    double duration_s{1.0};
};

// ---------------------------------------------------------------------------
class StaticTemporaryPhysics : public BasePhysics {
public:
    using BasePhysics::BasePhysics;

    void reset(const Command& cmd) override {
        start_cell = end_cell = cmd.params[0];
        curr_pos_m = board.cell_to_m(start_cell);
        start_ms   = cmd.timestamp;
    }

    std::optional<Command> update(int now_ms) override {
        double seconds = (now_ms - start_ms) / 1000.0;
        if(seconds >= param) {
            return std::optional<Command>{Command{now_ms, "", "done", {}}};
        }
        return std::nullopt;
    }

    bool is_movement_blocker() const override { return true; }
};

class JumpPhysics : public StaticTemporaryPhysics {
public:
    using StaticTemporaryPhysics::StaticTemporaryPhysics;
    bool can_be_captured() const override { return false; }
};

class RestPhysics : public StaticTemporaryPhysics {
public:
    using StaticTemporaryPhysics::StaticTemporaryPhysics;
    bool can_capture() const override { return false; }
}; 