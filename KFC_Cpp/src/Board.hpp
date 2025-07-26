#pragma once

#include "img/Img.hpp"
#include <utility>

class Board {
public:
    int cell_H_pix;
    int cell_W_pix;
    int W_cells;
    int H_cells;

    ImgPtr img;              // board image
    float cell_H_m;
    float cell_W_m;

public:
    Board(int cell_H_pix,
          int cell_W_pix,
          int W_cells,
          int H_cells,
          const ImgPtr& image,
          float cell_H_m = 1.0f,
          float cell_W_m = 1.0f);

    Board(const Board&) = default;
    Board(Board&&) noexcept = default;
    Board& operator=(const Board&) = default;
    Board& operator=(Board&&) noexcept = default;
    ~Board() = default;

    Board clone() const;                 // Deep-copy of image holder
    void show() const;                   // Show only if an image is loaded

    // Coordinate conversions -------------------------------------------------
    std::pair<int, int> m_to_cell(const std::pair<float, float>& pos_m) const;
    std::pair<float, float> cell_to_m(const std::pair<int, int>& cell) const;
    std::pair<int, int> m_to_pix(const std::pair<float, float>& pos_m) const;

}; 