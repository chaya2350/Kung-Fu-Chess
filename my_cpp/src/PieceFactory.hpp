#pragma once
#include "Board.hpp"
#include "Command.hpp"
#include "GraphicsFactory.hpp"
#include "Moves.hpp"
#include "PhysicsFactory.hpp"
#include "Piece.hpp"
#include "State.hpp"
#include <filesystem>
#include <fstream>
#include <sstream>
#include <map>
#include <string>
#include <memory>
#include <vector>
#include <iostream>
#include <nlohmann/json.hpp>

class PieceFactory {
public:
    const Board& board;
    std::shared_ptr<GraphicsFactory> graphics_factory;
    std::shared_ptr<PhysicsFactory> physics_factory;
    std::filesystem::path pieces_root;

    PieceFactory(const Board& board_, const std::filesystem::path& pieces_root_,
                 std::shared_ptr<GraphicsFactory> graphics_factory_ = nullptr,
                 std::shared_ptr<PhysicsFactory> physics_factory_ = nullptr)
        : board(board_),
          graphics_factory(graphics_factory_ ? graphics_factory_ : std::make_shared<GraphicsFactory>()),
          physics_factory(physics_factory_ ? physics_factory_ : std::make_shared<PhysicsFactory>(board_)),
          pieces_root(pieces_root_) {}

    static std::map<std::string, std::map<std::string, std::string>> _load_master_csv(const std::filesystem::path& pieces_root) {
        std::map<std::string, std::map<std::string, std::string>> _global_trans;
        auto csv_path = pieces_root / "transitions.csv";
        if (!std::filesystem::exists(csv_path)) return _global_trans;
        std::ifstream f(csv_path);
        std::string line;
        std::vector<std::string> headers;
        if (std::getline(f, line)) {
            std::istringstream iss(line);
            std::string col;
            while (std::getline(iss, col, ',')) headers.push_back(col);
        }
        while (std::getline(f, line)) {
            std::istringstream iss(line);
            std::string frm, ev, nxt;
            std::getline(iss, frm, ',');
            std::getline(iss, ev, ',');
            std::getline(iss, nxt, ',');
            _global_trans[frm][ev] = nxt;
        }
        return _global_trans;
    }

    std::shared_ptr<State> _build_state_machine(const std::filesystem::path& piece_dir, std::pair<int, int> cell) {
        // Always build a fresh state machine for each piece, with correct initial cell
        std::pair<int, int> board_size = {board.W_cells, board.H_cells};
        std::pair<int, int> cell_px = {board.cell_W_pix, board.cell_H_pix};
        auto _global_trans = _load_master_csv(piece_dir / "states");
        std::map<std::string, std::shared_ptr<State>> states;
        for (const auto& entry : std::filesystem::directory_iterator(piece_dir / "states")) {
            if (!entry.is_directory()) continue;
            std::string name = entry.path().filename().string();
            auto cfg_path = entry.path() / "config.json";
            nlohmann::json cfg;
            if (std::filesystem::exists(cfg_path)) {
                std::ifstream cfg_file(cfg_path);
                cfg_file >> cfg;
            }
            auto moves_path = entry.path() / "moves.txt";
            std::shared_ptr<Moves> moves = std::filesystem::exists(moves_path) ? std::make_shared<Moves>(moves_path.string(), board_size) : nullptr;
            // Always create a fresh graphics and physics pointer for each state
            auto graphics_ptr = graphics_factory->load(entry.path() / "sprites", cfg.value("graphics", nlohmann::json::object()), cell_px);
            auto physics_cfg = cfg.value("physics", nlohmann::json::object());
            auto physics_ptr = physics_factory->create(cell, name, physics_cfg);
            physics_ptr->do_i_need_clear_path = physics_cfg.value("need_clear_path", true);
            auto st = std::make_shared<State>(
                moves,
                std::shared_ptr<Graphics>(std::move(graphics_ptr)),
                std::move(physics_ptr)
            );
            st->name = name;
            states[name] = st;
        }
        for (const auto& [frm, ev_map] : _global_trans) {
            auto src = states.find(frm);
            if (src == states.end()) continue;
            for (const auto& [ev, nxt] : ev_map) {
                auto dst = states.find(nxt);
                if (dst == states.end()) continue;
                src->second->set_transition(ev, dst->second);
            }
        }
        // Ensure all states' physics are initialized with the correct cell
        for (auto& [name, st] : states) {
            if (st && st->physics) {
                std::vector<int> cell_vec{cell.first, cell.second};
                // אם הפיזיקה היא MovePhysics, נאתחל עם שני וקטורים
                if (dynamic_cast<MovePhysics*>(st->physics.get())) {
                    Command init_cmd(0, "", "move", {cell_vec, cell_vec});
                    st->reset(init_cmd);
                } else {
                    Command init_cmd(0, "", "idle", {cell_vec});
                    st->reset(init_cmd);
                }
            }
        }
        auto it = states.find("idle");
        return (it != states.end()) ? it->second : nullptr;
    }

    std::shared_ptr<Piece> create_piece(const std::string& p_type, std::pair<int, int> cell) {
        auto p_dir = pieces_root / p_type;
        // Build a fresh state machine for each piece, and inject the initial cell
        auto state = _build_state_machine(p_dir, cell);
        auto piece = std::make_shared<Piece>(p_type + "_" + std::to_string(cell.first) + "," + std::to_string(cell.second), state);
        // Pass the initial cell to the state/physics for correct initialization
        if (piece->state && piece->state->physics) {
            std::vector<int> cell_vec{cell.first, cell.second};
            if (dynamic_cast<MovePhysics*>(piece->state->physics.get())) {
                Command init_cmd(0, piece->id, "move", {cell_vec, cell_vec});
                piece->state->reset(init_cmd);
            } else {
                Command init_cmd(0, piece->id, "idle", {cell_vec});
                piece->state->reset(init_cmd);
            }
        }
        return piece;
    }
};
