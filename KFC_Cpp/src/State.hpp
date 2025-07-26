#pragma once

#include "Moves.hpp"
#include "Graphics.hpp"
#include "Physics.hpp"
#include <unordered_map>
#include <memory>
#include <string>
#include <cctype>

class State : public std::enable_shared_from_this<State> {
public:
    State(std::shared_ptr<Moves> moves,
          std::shared_ptr<Graphics> graphics,
          std::shared_ptr<BasePhysics> physics)
        : moves(moves), graphics(graphics), physics(physics) {}

    std::shared_ptr<Moves>    moves;
    std::shared_ptr<Graphics> graphics;
    std::shared_ptr<BasePhysics> physics;

    std::unordered_map<std::string, std::weak_ptr<State>> transitions;
    std::string name;

    void set_transition(const std::string& event, const std::shared_ptr<State>& target) { transitions[event] = target; }

    void reset(const Command& cmd) {
        graphics->reset(cmd);
        physics->reset(cmd);
    }

    std::shared_ptr<State> on_command(const Command& cmd) {
        std::string key = cmd.type;
        for(auto& ch : key) ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
        auto it = transitions.find(key);
        if(it != transitions.end()) {
            if(auto next = it->second.lock()) {
                next->reset(cmd);
                return next;
            }
        }
        return shared_from_this();
    }

    std::shared_ptr<State> update(int now_ms) {
        auto internal = physics->update(now_ms);
        if(internal) {
            return on_command(*internal);
        }
        return shared_from_this();
    }

    bool can_be_captured() const { return physics->can_be_captured(); }
    bool can_capture()    const { return physics->can_capture(); }
}; 