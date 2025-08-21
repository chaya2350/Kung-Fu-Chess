
#pragma once
#include <vector>
#include <string>
#include "Img.hpp"

class MockImg {
public:
    MockImg() : W(0), H(0) {}

    MockImg& read(const std::string& path,
                  std::pair<int, int> size = std::make_pair(-1, -1),
                  bool keep_aspect = false,
                  int interpolation = 0) {
        W = size.first;
        H = size.second;
        return *this;
    }

    MockImg& copy() {
        return *this;
    }

    void draw_on(MockImg& other, int x, int y) {
        traj.emplace_back(x, y);
    }

    void put_text(const std::string& txt, int x, int y, double font_size, int thickness = 1) {
        txt_traj.emplace_back(std::make_pair(std::make_pair(x, y), txt));
    }

    void show() {}

    int W;
    int H;
    std::vector<std::pair<int, int>> traj;
    std::vector<std::pair<std::pair<int, int>, std::string>> txt_traj;
};

inline MockImg mock_graphics_image_loader(const std::string& path, std::pair<int, int> size, bool keep_aspect = false) {
    return MockImg();
}
