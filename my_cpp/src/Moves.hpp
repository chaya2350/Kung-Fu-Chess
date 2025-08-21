#pragma once
#include <string>
#include <vector>
#include <tuple>
#include <map>
#include <fstream>
#include <sstream>
#include <iostream>
#include <algorithm>
#include <cmath>
#include <memory>

class Piece;

class Moves {
public:
    std::pair<int, int> dims;
    std::map<std::pair<int, int>, std::string> moves;

    Moves(const std::string& moves_file, std::pair<int, int> dims_)
        : dims(dims_) {
        std::ifstream f(moves_file);
        if (!f.is_open()) return;
        std::string line;
        while (std::getline(f, line)) {
            line.erase(0, line.find_first_not_of(" \t\n\r"));
            line.erase(line.find_last_not_of(" \t\n\r") + 1);
            if (line.empty() || line[0] == '#') continue;
            auto comment_pos = line.find('#');
            if (comment_pos != std::string::npos) line = line.substr(0, comment_pos);
            auto colon_pos = line.find(':');
            std::string move = line.substr(0, colon_pos);
            std::string tag = (colon_pos != std::string::npos) ? line.substr(colon_pos + 1) : "";
            move.erase(0, move.find_first_not_of(" \t"));
            move.erase(move.find_last_not_of(" \t") + 1);
            int dr, dc;
            char comma;
            std::istringstream iss(move);
            iss >> dr >> comma >> dc;
            tag.erase(0, tag.find_first_not_of(" \t"));
            tag.erase(tag.find_last_not_of(" \t") + 1);
            moves[std::make_pair(dr, dc)] = tag;
        }
    }

    static std::tuple<int, int, int> parse(const std::string& s) {
        auto colon_pos = s.find(':');
        if (colon_pos == std::string::npos) {
            throw std::runtime_error("Unsupported move syntax: ':' required");
        }
        std::string coords = s.substr(0, colon_pos);
        std::string tag_str = s.substr(colon_pos + 1);
        int dr, dc;
        char comma;
        std::istringstream iss(coords);
        iss >> dr >> comma >> dc;
        int tag = -1;
        if (tag_str == "capture") tag = 1;
        else if (tag_str == "non_capture") tag = 0;
        return std::make_tuple(dr, dc, tag);
    }

    bool is_dst_cell_valid(int dr, int dc, const std::vector<std::shared_ptr<Piece>>* dst_pieces = nullptr, const std::string* my_color = nullptr, const bool* dst_has_piece = nullptr) const {
        if (dst_has_piece && !dst_pieces) {
            // Dummy piece logic omitted for C++
        }
        auto it = moves.find(std::make_pair(dr, dc));
        if (it == moves.end()) return false;
        const std::string& move_tag = it->second;
        if (move_tag.empty()) {
            if (dst_pieces) {
                // Can't check friendly_pieces without knowing piece structure
                // User should implement this logic
            }
            return true;
        }
        if (move_tag == "capture") {
            // User should implement: check if dst_pieces has enemy pieces
            return dst_pieces && !dst_pieces->empty();
        }
        if (move_tag == "non_capture") {
            return !dst_pieces;
        }
        return false;
    }

    bool is_valid(const std::pair<int, int>& src_cell, const std::pair<int, int>& dst_cell, const std::map<std::pair<int, int>, std::vector<std::shared_ptr<Piece>>>& cell2piece, bool is_need_clear_path, const std::string& my_color) const {
        if (!(0 <= dst_cell.first && dst_cell.first < dims.first && 0 <= dst_cell.second && dst_cell.second < dims.second))
            return false;
        int dr = dst_cell.first - src_cell.first;
        int dc = dst_cell.second - src_cell.second;
        auto it = cell2piece.find(dst_cell);
        const std::vector<std::shared_ptr<Piece>>* dst_pieces = (it != cell2piece.end()) ? &it->second : nullptr;
        if (!is_dst_cell_valid(dr, dc, dst_pieces, &my_color))
            return false;
        if (is_need_clear_path && !_path_is_clear(src_cell, dst_cell, cell2piece, my_color))
            return false;
        return true;
    }

    bool _path_is_clear(const std::pair<int, int>& src_cell, const std::pair<int, int>& dst_cell, const std::map<std::pair<int, int>, std::vector<std::shared_ptr<Piece>>>& cell2piece, const std::string& my_color) const {
        int dr = dst_cell.first - src_cell.first;
        int dc = dst_cell.second - src_cell.second;
        int steps = std::max(std::abs(dr), std::abs(dc));
        if (steps == 0) return true;
        float step_r = dr / static_cast<float>(steps);
        float step_c = dc / static_cast<float>(steps);
        for (int i = 1; i < steps; ++i) {
            int r = src_cell.first + static_cast<int>(i * step_r);
            int c = src_cell.second + static_cast<int>(i * step_c);
            if (cell2piece.find(std::make_pair(r, c)) != cell2piece.end()) {
                std::cout << "Path not clear at (" << r << "," << c << ") - piece blocking" << std::endl;
                return false;
            }
        }
        return true;
    }
};
