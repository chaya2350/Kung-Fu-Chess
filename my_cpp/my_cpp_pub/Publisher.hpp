#pragma once
#include "Listener.hpp"
#include <string>
#include <map>
#include <stdexcept>

class Publisher {
public:
    std::map<std::string, std::map<std::string, Listener*>> _channels;

    Publisher() {
        _channels["moves"] = {};
        _channels["score"] = {};
        // _channels["sounds"] = {};
    }

    void new_listener(const std::string& id, const std::string& channel, Listener* listener) {
        if (_channels.find(channel) == _channels.end()) {
            throw std::runtime_error("Channel " + channel + " does not exist.");
        }
        _channels[channel][id] = listener;
    }

    void publish(const std::string& channel, const std::string& id, const std::string& message) {
        _channels[channel][id]->listening(message);
    }
};
