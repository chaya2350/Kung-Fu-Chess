#pragma once
#include <string>

class Publisher; // Forward declaration

class Listener {
public:
    Listener(const std::string& id, const std::string& channel, Publisher* publisher);
    virtual ~Listener() = default;
    virtual void listening(const std::string& message) = 0;
};
