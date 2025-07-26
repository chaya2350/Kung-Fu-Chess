#pragma once

#include "Piece.hpp"
#include "PhysicsFactory.hpp"
#include "GraphicsFactory.hpp"
#include <unordered_map>
#include <string>
#include <memory>
#include <optional>
#include "nlohmann/json.hpp"

class PieceFactory {
public:
    PieceFactory(Board& board,
                 const std::string& pieces_root,
                 const GraphicsFactory& gfx_factory)
        : board(board), pieces_root(pieces_root), gfx_factory(gfx_factory) {}

    PiecePtr create_piece(const std::string& type_name,
                                        const std::pair<int,int>& cell) {
        // Generate unique id for this type
        int &counter = id_counters[type_name];
        ++counter;
        std::string id = type_name + "_" + std::to_string(counter);

        // Create physics states
        PhysicsFactory phys_factory(board);
        auto idle_phys = phys_factory.create(cell, "idle", {});
        auto move_phys = phys_factory.create(cell, "move", nlohmann::json{});
        auto jump_phys = phys_factory.create(cell, "jump", nlohmann::json{});

        // Graphics – placeholder cell size 32x32
        auto gfx_idle  = gfx_factory.load("", {}, {32,32});
        auto gfx_other = gfx_factory.load("", {}, {32,32});

        auto idle = std::make_shared<State>(nullptr, gfx_idle,  idle_phys);
        auto move = std::make_shared<State>(nullptr, gfx_other, move_phys);
        auto jump = std::make_shared<State>(nullptr, gfx_other, jump_phys);

        idle->name = "idle";
        move->name = "move";
        jump->name = "jump";

        idle->set_transition("move", move);
        idle->set_transition("jump", jump);
        move->set_transition("done", idle);
        jump->set_transition("done", idle);

        auto piece = std::make_shared<Piece>(id, idle);
        // initialise position
        idle->reset(Command{0, id, "idle", {cell}});
        return piece;
    }
private:
    Board& board;
    std::string pieces_root;
    const GraphicsFactory& gfx_factory;
    std::unordered_map<std::string,int> id_counters;
}; 