
#pragma once
#include "Command.hpp"
#include <map>
#include <string>
#include <vector>
#include <mutex>
#include <thread>
#include <iostream>
#include <algorithm>
#include <queue>
#include <chrono>

// Forward declaration
class KeyboardProcessor;

// KeyboardProducer: runs in a thread, listens for keypresses, pushes Commands
class KeyboardProducer {
public:
    bool running;
    std::thread th;
    KeyboardProcessor* kp;
    std::queue<Command>* queue;
    int player;

    KeyboardProducer(KeyboardProcessor* kp_, std::queue<Command>* q, int player_)
        : running(false), kp(kp_), queue(q), player(player_) {}

    void start() {
        running = true;
        th = std::thread([this]() { this->run(); });
    }
    void stop() {
        running = false;
        if (th.joinable()) th.join();
    }
    void run() {
        // TODO: Implement real keyboard input loop (platform-specific)
        // For now, this is a stub.
        while (running) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    }
};

class KeyboardProcessor {
public:
    int rows, cols;
    std::map<std::string, std::string> keymap;
    std::vector<int> cursor; // [row, col]
    std::mutex lock;

    KeyboardProcessor(int rows_, int cols_, const std::map<std::string, std::string>& keymap_)
        : rows(rows_), cols(cols_), keymap(keymap_), cursor{0, 0} {}

    std::string process_key(const std::string& event_type, const std::string& key) {
        // Only care about key-down events
        if (event_type != "down") return "";
        auto it = keymap.find(key);
        std::string action = (it != keymap.end()) ? it->second : "";
        // std::cout << "Key '" << key << "' -> action '" << action << "'\n";
        if (action == "up" || action == "down" || action == "left" || action == "right") {
            std::lock_guard<std::mutex> guard(lock);
            int& r = cursor[0];
            int& c = cursor[1];
            if (action == "up") r = std::max(0, r - 1);
            else if (action == "down") r = std::min(rows - 1, r + 1);
            else if (action == "left") c = std::max(0, c - 1);
            else if (action == "right") c = std::min(cols - 1, c + 1);
            // std::cout << "Cursor moved to (" << r << "," << c << ")\n";
        }
        return action;
    }

    std::pair<int, int> get_cursor() {
        std::lock_guard<std::mutex> guard(lock);
        return {cursor[0], cursor[1]};
    }
};

// Note: KeyboardProducer is not implemented due to lack of cross-platform keyboard event library in standard C++.
// You can implement a similar class using a platform-specific library or a GUI framework.
