#pragma once
#include "Command.hpp"
#include "Graphics.hpp"
#include "Moves.hpp"
#include "Physics.hpp"
#include <iostream>
#include <map>
#include <memory>
#include <string>
#include <utility>


class State {
  State(const State&) = delete;
  State& operator=(const State&) = delete;
  State(State&&) = delete;
  State& operator=(State&&) = delete;
public:
  virtual ~State() = default;
  std::shared_ptr<Moves> moves;
  std::shared_ptr<Graphics> graphics;
  std::unique_ptr<BasePhysics> physics;
  std::map<std::string, std::shared_ptr<State>> transitions;
  std::string name;

  State(std::shared_ptr<Moves> moves_, std::shared_ptr<Graphics> graphics_,
        std::unique_ptr<BasePhysics> physics_)
      : moves(std::move(moves_)), graphics(std::move(graphics_)), physics(std::move(physics_)), name("") {
    if (physics) {
    } else {
    }
  }

  std::string repr() const { return "State(" + name + ")"; }

  void set_transition(const std::string &event, std::shared_ptr<State> target) {
    transitions[event] = target;
  }


  bool reset(const Command &cmd) {
    graphics->reset(cmd);
    return physics->reset(cmd);
  }


  // Overload for on_command with 2 arguments (for update)
  std::pair<std::shared_ptr<State>, bool> on_command(
      const Command &cmd,
      const std::map<std::pair<int, int>, std::vector<std::shared_ptr<Piece>>> *cell2piece) {
    return on_command(cmd, cell2piece, "");
  }

  std::pair<std::shared_ptr<State>, bool> on_command(
      const Command &cmd,
      const std::map<std::pair<int, int>, std::vector<std::shared_ptr<Piece>>>
          *cell2piece,
      const std::string &my_color) {
    auto it = transitions.find(cmd.type);
    if (it == transitions.end()) {
      return std::make_pair(std::shared_ptr<State>(this), false);
    }
    auto nxt = it->second;
    if (cmd.type == "move") {
      if (!moves || cmd.params.size() < 2) {
        throw std::runtime_error("Invalid move command");
      }
      auto src_cell = std::any_cast<std::pair<int, int>>(cmd.params[0]);
      auto dst_cell = std::any_cast<std::pair<int, int>>(cmd.params[1]);
      if (src_cell != physics->get_curr_cell()) {
        throw std::runtime_error("source cell is not the current cell");
      }
      if (!moves->is_valid(
              src_cell, dst_cell,
              cell2piece ? *cell2piece
                         : std::map<std::pair<int, int>,
                                    std::vector<std::shared_ptr<Piece>>>(),
              physics->is_need_clear_path(), my_color)) {
        std::cout << "Invalid move: (" << src_cell.first << ","
                  << src_cell.second << ") -> (" << dst_cell.first << ","
                  << dst_cell.second << ")" << std::endl;
        return std::make_pair(std::shared_ptr<State>(this), false);
      }
    }
    std::cout << "[TRANSITION] " << cmd.type << ": " << repr() << " ? "
              << nxt->repr() << std::endl;
    bool flag = nxt->reset(cmd);
    return std::make_pair(nxt, flag);
  }

  std::pair<std::shared_ptr<State>, bool> update(int now_ms) {
    auto internal = physics->update(now_ms);
    if (internal) {
      std::cout << "[DBG] internal: " << internal->type << std::endl;
      return on_command(*internal, nullptr);
    }
    graphics->update(now_ms);
    return std::make_pair(std::shared_ptr<State>(this), false);
  }

  bool can_be_captured() const { return physics->can_be_captured(); }

  bool can_capture() const { return physics->can_capture(); }
};
