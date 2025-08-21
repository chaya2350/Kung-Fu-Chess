#ifndef GAMELOG_HPP
#define GAMELOG_HPP

#include <string>
#include <vector>
#include "../my_cpp/src/Command.hpp"
#include "Listener.hpp"

class Publisher; // Forward declaration


class GameLog : public Listener {
public:
    GameLog(const std::string& color, Publisher* publisher)
        : Listener(color, "moves", publisher) {}

    // Required by Listener interface
    void listening(const std::string& message) override {
        _log.push_back(message);
    }

    void add(const std::string& message) {
        _log.push_back(message);
    }

    std::vector<std::string> get_log() const {
        return _log;
    }

protected:
    std::vector<std::string> _log;
};

#endif // GAMELOG_HPP
