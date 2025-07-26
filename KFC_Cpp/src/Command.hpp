#pragma once

#include <string>
#include <vector>

struct Command {
    int timestamp;                 // ms since game start
    std::string piece_id;          // identifier of the piece (may be empty)
    std::string type;              // e.g., "move", "jump", "done"...
    std::vector<std::pair<int,int>> params;  // payload – board cells etc.

    Command(int ts, std::string pid, std::string t, std::vector<std::pair<int,int>> p)
        : timestamp(ts), piece_id(pid), type(t), params(p) {}
}; 