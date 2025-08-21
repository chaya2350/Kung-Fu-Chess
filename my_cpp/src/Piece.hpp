#pragma once
#include "Board.hpp"
#include <string>
#include <vector>
#include <map>
#include <memory>
#include <utility>
#include <cstdint>
#include "Command.hpp"
#include "State.hpp"

class Piece {
    Piece(const Piece&) = delete;
    Piece& operator=(const Piece&) = delete;
    Piece(Piece&&) = delete;
    Piece& operator=(Piece&&) = delete;
public:
    std::string id;
    std::shared_ptr<State> state;

    Piece(const std::string& piece_id, std::shared_ptr<State> init_state)
        : id(piece_id), state(init_state) {
        if (!state) std::cout << " (state is nullptr)";
        else if (!state->physics) std::cout << " (physics is nullptr)";
        std::cout << std::endl;
    }

    bool on_command(const Command& cmd, std::map<std::pair<int, int>, std::vector<std::shared_ptr<Piece>>>& cell2piece);

    bool reset(int start_ms) {
        auto cell = current_cell();
        std::vector<int> cell_vec{cell.first, cell.second};
        bool flag = state->reset(Command(start_ms, id, "idle", {cell_vec}));
        return flag;
    }

    bool update(int now_ms) {
        bool flag;
        std::shared_ptr<State> new_state;
        std::tie(new_state, flag) = state->update(now_ms);
        state = new_state;
        return flag;
    }

    bool is_movement_blocker() const {
        return state->physics->is_movement_blocker();
    }

    void draw_on_board(const Board& board, int now_ms) {
        if (!state || !state->physics || !state->graphics) return;
        
        try {
            auto pos = state->physics->get_pos_pix();
            int x = pos.first;
            int y = pos.second;
            if (x == std::numeric_limits<int>::min() || y == std::numeric_limits<int>::min()) {
                return;
            }
            auto sprite_const = state->graphics->get_img();
            Img sprite = sprite_const;
            int center_offset_x = (board.cell_W_pix - sprite.img.cols) / 2;
            int center_offset_y = (board.cell_H_pix - sprite.img.rows) / 2;
            int centered_x = x + center_offset_x;
            int centered_y = y + center_offset_y;
            sprite.draw_on(const_cast<Img&>(board.img), centered_x, centered_y);
        } catch (...) {
            // שגיאה בציור
        }
    }

    std::pair<int, int> current_cell() const {
        if (!state || !state->physics) return {0,0};
        try {
            return state->physics->get_curr_cell();
        } catch (...) {
            return {0, 0};
        }
    }
};
