#pragma once
#include <string>
#include <vector>
#include <any>
#include <sstream>
#include <iostream>
#include <typeinfo>
#include <utility>

class Command {
public:
    int timestamp;           // ms since game start
    std::string piece_id;
    std::string type;        // "move" | "jump" | ...

    std::vector<std::any> params; // payload (can be string, pair, vector, etc.)

    Command(int timestamp_, const std::string& piece_id_, const std::string& type_, const std::vector<std::any>& params_)
        : timestamp(timestamp_), piece_id(piece_id_), type(type_), params(params_) {}

    std::string to_string() const {
        std::ostringstream oss;
        oss << "Command(timestamp=" << timestamp
            << ", piece_id=" << piece_id
            << ", type=" << type
            << ", params=[";
        for (size_t i = 0; i < params.size(); ++i) {
            if (params[i].type() == typeid(std::string)) {
                oss << std::any_cast<std::string>(params[i]);
            } else if (params[i].type() == typeid(int)) {
                oss << std::any_cast<int>(params[i]);
            } else if (params[i].type() == typeid(std::vector<int>)) {
                auto v = std::any_cast<std::vector<int>>(params[i]);
                oss << "[";
                for (size_t j = 0; j < v.size(); ++j) {
                    oss << v[j];
                    if (j + 1 < v.size()) oss << ",";
                }
                oss << "]";
            } else if (params[i].type() == typeid(std::pair<int, int>)) {
                auto p = std::any_cast<std::pair<int, int>>(params[i]);
                oss << "(" << p.first << "," << p.second << ")";
            } else {
                oss << "<unknown>";
            }
            if (i + 1 < params.size()) oss << ", ";
        }
        oss << "]";
        return oss.str();
    }

    friend std::ostream& operator<<(std::ostream& os, const Command& cmd) {
        return os << cmd.to_string();
    }
};
