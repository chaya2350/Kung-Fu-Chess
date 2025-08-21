
#include "Piece.hpp"
#include "Board.hpp"
#include <string>
#include <map>
#include <vector>
#include <memory>
#include <utility>

bool Piece::on_command(const Command& cmd, std::map<std::pair<int, int>, std::vector<std::shared_ptr<Piece>>>& cell2piece) {
    if (!state) {
        std::cout << "[ERROR] Piece::on_command: state nullptr for " << id << std::endl;
        return false;
    }
    char my_color = id[1];
    std::string my_color_str(1, my_color);
    bool flag;
    std::shared_ptr<State> new_state;
    std::tie(new_state, flag) = state->on_command(cmd, &cell2piece, my_color_str);
    state = new_state;
    return flag;
}
