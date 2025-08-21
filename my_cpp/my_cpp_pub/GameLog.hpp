#ifndef GAMELOG_HPP
#define GAMELOG_HPP

#include <string>
#include <vector>
#include "../KFC_Py/Command.hpp"
#include "Listener.hpp"

class Publisher; // Forward declaration

class GameLog : public Listener {
public:
    GameLog(const std::string& color, Publisher* publisher)
        : Listener(color, "moves", publisher) {}

    void listening(const Command& cmd) override {
        _log.push_back(_processing_message(cmd));
    }

    std::string format_millis(int millis) const {
        int seconds = millis / 1000;
        int ms = millis % 1000;
        int minutes = seconds / 60;
        int sec = seconds % 60;
        int hours = minutes / 60;
        int min_ = minutes % 60;
        // char buf[16];
        // snprintf(buf, sizeof(buf), "%02d:%02d:%02d.%03d", hours, min_, sec, ms);
        char buf[16];
        snprintf(buf, sizeof(buf), "%02d:%02d:%02d", hours, min_, sec);
        return std::string(buf);
    }

    std::vector<std::string> get_log() const {
        return _log;
    }

protected:
    std::string _processing_message(const Command& cmd) const {
        // {self.format_millis(cmd.timestamp)}, {cmd.piece_id[:2]}{cmd.piece_id[7]}, {chr(cmd.params[0][0] + ord('a'))}{ cmd.params[0][1]} -> {chr(cmd.params[1][0] + ord('a'))}{ cmd.params[1][1]}
        std::string millis_str = format_millis(cmd.timestamp);
        std::string piece_id = cmd.piece_id.substr(0, 2) + cmd.piece_id.substr(7, 1);
        char from_col = static_cast<char>(cmd.params[0][0] + 'a');
        int from_row = cmd.params[0][1];
        char to_col = static_cast<char>(cmd.params[1][0] + 'a');
        int to_row = cmd.params[1][1];
        char buf[64];
        snprintf(buf, sizeof(buf), "%s, %s, %c%d -> %c%d", millis_str.c_str(), piece_id.c_str(), from_col, from_row, to_col, to_row);
        return std::string(buf);
    }

    std::vector<std::string> _log;
};

#endif // GAMELOG_HPP
