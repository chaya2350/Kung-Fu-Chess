#pragma once
#include "Board.hpp"
#include "Command.hpp"
#include "Sound.hpp"
#include <cmath>
#include <vector>
#include <memory>
#include <algorithm>
#include <any>
#include <iostream>
#include <utility>

class BasePhysics {
public:
    const Board& board;
    std::vector<int> _start_cell;
    std::vector<int> _end_cell;
    std::vector<float> _curr_pos_m;
    float param;
    int _start_ms;
    bool do_i_need_clear_path;

    BasePhysics(const Board& board_, float param_ = 1.0f)
        : board(board_), param(param_), _start_ms(0), do_i_need_clear_path(true), _curr_pos_m{0.0f, 0.0f} {
    }

    virtual ~BasePhysics() = default; // Destructor is already defined

    virtual bool reset(const Command& cmd) = 0;
    virtual std::unique_ptr<Command> update(int now_ms) = 0;

    std::vector<float> get_pos_m() const {
        return _curr_pos_m;
    }
    std::pair<int, int> get_pos_pix() const {
        if (_curr_pos_m.size() < 2) return {0,0};
        try {
            return board.m_to_pix({_curr_pos_m[0], _curr_pos_m[1]});
        } catch (...) {
            return {0,0};
        }
    }
    virtual std::pair<int, int> get_curr_cell() const {
        if (_curr_pos_m.size() < 2) return {0,0};
        int row = static_cast<int>(std::round(_curr_pos_m[0]));
        int col = static_cast<int>(std::round(_curr_pos_m[1]));
        return {row, col};
    }
    int get_start_ms() const { return _start_ms; }
    virtual bool can_be_captured() const { return true; }
    virtual bool can_capture() const { return true; }
    virtual bool is_movement_blocker() const { return false; }
    bool is_need_clear_path() const { return do_i_need_clear_path; }
};

class IdlePhysics : public BasePhysics {
public:
    IdlePhysics(const Board& board_, float param_ = 1.0f) : BasePhysics(board_, param_) {}
    bool reset(const Command& cmd) override {
        if (cmd.params.empty()) {
            return false;
        }
        try {
            auto cell_vec = std::any_cast<std::vector<int>>(cmd.params[0]);
            if (cell_vec.size() < 2) {
                return false;
            }
            _end_cell = _start_cell = cell_vec;
            // Use cell coordinates directly as "meters" to avoid precision issues
            _curr_pos_m = {static_cast<float>(_start_cell[0]), static_cast<float>(_start_cell[1])};

            _start_ms = cmd.timestamp;
        } catch (const std::bad_any_cast& e) {
            return false;
        }
        return true;
    }
    std::unique_ptr<Command> update(int /*now_ms*/) override { return nullptr; }
    bool can_capture() const override { return false; }
    bool is_movement_blocker() const override { return true; }
};

class MovePhysics : public BasePhysics {
public:
    Sound sound;
    float _speed_m_s;
    std::vector<float> _movement_vector;
    float _movement_vector_length;
    float _duration_s;

    MovePhysics(const Board& board_, float param_ = 1.0f)
        : BasePhysics(board_, param_), sound(), _speed_m_s(param_) {
        if (_speed_m_s == 0) throw std::runtime_error("_speed_m_s is 0");
        if (_speed_m_s < 0) _speed_m_s = std::abs(_speed_m_s);
    }
    bool can_be_captured() const override { return false; }
    bool reset(const Command& cmd) override {
        for (size_t i = 0; i < cmd.params.size(); ++i) {
        }
        // sound.play("../../sounds/foot_step.wav"); // Removed - sound handled by Game class
        // Defensive: check params size
        if (cmd.params.size() < 2) {
            return false;
        }
        // Defensive: check any_cast and vector size
        try {
            _start_cell = std::any_cast<std::vector<int>>(cmd.params[0]);
            _end_cell = std::any_cast<std::vector<int>>(cmd.params[1]);
        } catch (const std::bad_any_cast& e) {
            return false;
        }
        if (_start_cell.size() < 2 || _end_cell.size() < 2) {
            return false;
        }
        for (size_t i = 0; i < _start_cell.size(); ++i) {
            std::cout << _start_cell[i];
            if (i + 1 < _start_cell.size()) std::cout << ", ";
        }
        std::cout << "]\n";
        for (size_t i = 0; i < _end_cell.size(); ++i) {
            std::cout << _end_cell[i];
            if (i + 1 < _end_cell.size()) std::cout << ", ";
        }
        std::cout << "]\n";
        _curr_pos_m = {static_cast<float>(_start_cell[0]), static_cast<float>(_start_cell[1])};
        _start_ms = cmd.timestamp;
        std::vector<float> start_pos = {static_cast<float>(_start_cell[0]), static_cast<float>(_start_cell[1])};
        std::vector<float> end_pos = {static_cast<float>(_end_cell[0]), static_cast<float>(_end_cell[1])};
        _movement_vector = {end_pos[0] - start_pos[0], end_pos[1] - start_pos[1]};
        _movement_vector_length = std::hypot(_movement_vector[0], _movement_vector[1]);
        if (_movement_vector_length == 0.0f) {
            return false;
        }
        _movement_vector[0] /= _movement_vector_length;
        _movement_vector[1] /= _movement_vector_length;
        _duration_s = _movement_vector_length / _speed_m_s;
        return true;
    }
    std::unique_ptr<Command> update(int now_ms) override {
        float seconds_passed = (now_ms - _start_ms) / 1000.0f;
        if (_curr_pos_m.size() < 2 || _movement_vector.size() < 2) {
            std::cout << "[ERROR] MovePhysics::update: vector too small! _curr_pos_m.size()=" << _curr_pos_m.size() << ", _movement_vector.size()=" << _movement_vector.size() << std::endl;
            return nullptr;
        }
        // Calculate position based on distance traveled from start, not incremental addition
        float distance_traveled = std::min(seconds_passed * _speed_m_s, _movement_vector_length);
        _curr_pos_m[0] = static_cast<float>(_start_cell[0]) + _movement_vector[0] * distance_traveled;
        _curr_pos_m[1] = static_cast<float>(_start_cell[1]) + _movement_vector[1] * distance_traveled;
        if (seconds_passed >= _duration_s) {
            sound.stop();
            return std::make_unique<Command>(now_ms, "", "done", std::vector<std::any>{});
        }
        return nullptr;
    }
    std::vector<float> get_pos_m() const { return _curr_pos_m; }
    std::pair<int, int> get_pos_pix() const { return BasePhysics::get_pos_pix(); }
};

class StaticTemporaryPhysics : public BasePhysics {
public:
    float duration_s;
    StaticTemporaryPhysics(const Board& board_, float param_ = 1.0f) : BasePhysics(board_, param_), duration_s(param_) {
    }
    bool reset(const Command& cmd) override {
        _end_cell = _start_cell = std::any_cast<std::vector<int>>(cmd.params[0]);
        _curr_pos_m = {static_cast<float>(_start_cell[0]), static_cast<float>(_start_cell[1])};
        _start_ms = cmd.timestamp;
        return false;
    }
    std::unique_ptr<Command> update(int now_ms) override {
        float seconds_passed = (now_ms - _start_ms) / 1000.0f;
        if (seconds_passed >= duration_s) {
            return std::make_unique<Command>(now_ms, "", "done", std::vector<std::any>{});
        }
        return nullptr;
    }
};

class JumpPhysics : public StaticTemporaryPhysics {
public:
    JumpPhysics(const Board& board_, float param_ = 1.0f) : StaticTemporaryPhysics(board_, param_) {
    }
    bool reset(const Command& cmd) override {
        if (cmd.params.size() == 1) {
            StaticTemporaryPhysics::reset(cmd);
            return false;
        }
        _start_cell = std::any_cast<std::vector<int>>(cmd.params[0]);
        _end_cell = std::any_cast<std::vector<int>>(cmd.params[1]);
        _curr_pos_m = {static_cast<float>(_end_cell[0]), static_cast<float>(_end_cell[1])};
        _start_ms = cmd.timestamp;
        return false;
    }
    bool can_be_captured() const override { return false; }
};

class RestPhysics : public StaticTemporaryPhysics {
public:
    RestPhysics(const Board& board_, float param_ = 1.0f) : StaticTemporaryPhysics(board_, param_) {
    }
    bool can_capture() const override { return false; }
    bool is_movement_blocker() const override { return true; }
};
