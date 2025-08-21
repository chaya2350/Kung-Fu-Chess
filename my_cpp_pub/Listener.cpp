#include "Listener.hpp"
#include "Publisher.hpp"

Listener::Listener(const std::string& id, const std::string& channel, Publisher* publisher) {
    publisher->new_listener(id, channel, this);
}
