#pragma once
#include "Board.hpp"
#include "Physics.hpp"
#include <string>
#include <memory>
#include <algorithm>
#include <map>
#include <nlohmann/json.hpp>

class PhysicsFactory {
public:
    const Board& board;
    PhysicsFactory(const Board& board_) : board(board_) {}

    std::unique_ptr<BasePhysics> create(const std::pair<int, int>& start_cell, const std::string& state_name, const nlohmann::json& cfg) {
        float speed = 0.0f;
        if (cfg.contains("speed_m_per_sec")) speed = cfg["speed_m_per_sec"].get<float>();

        std::string name_l = state_name;
        std::transform(name_l.begin(), name_l.end(), name_l.begin(), ::tolower);
        if (name_l == "move") {
            return std::make_unique<MovePhysics>(board, speed);
        } else if (name_l == "jump") {
            return std::make_unique<JumpPhysics>(board, speed);
        } else if (name_l.size() >= 4 && name_l.substr(name_l.size()-4) == "rest" || name_l == "rest") {
            float duration_ms = 3000.0f;
            if (cfg.contains("duration_ms")) duration_ms = cfg["duration_ms"].get<float>();
            return std::make_unique<RestPhysics>(board, duration_ms / 1000.0f);
        } else {
            return std::make_unique<IdlePhysics>(board, speed);
        }
    }
};
