#include "Board.hpp"

#include <cmath>    // std::round

// ---------------------------------------------------------------------------
// Constructor
// ---------------------------------------------------------------------------
Board::Board(int cell_H_pix_,
             int cell_W_pix_,
             int W_cells_,
             int H_cells_,
             const Img& image,
             float cell_H_m_,
             float cell_W_m_)
    : cell_H_pix(cell_H_pix_),
      cell_W_pix(cell_W_pix_),
      W_cells(W_cells_),
      H_cells(H_cells_),
      img(image),
      cell_H_m(cell_H_m_),
      cell_W_m(cell_W_m_) {}

// ---------------------------------------------------------------------------
Board Board::clone() const {
    Img new_img = img;  // cv::Mat uses reference counting – shallow copy OK
    // If deep-copy is required uncomment: new_img = Img(img); but fine for now.
    return Board(cell_H_pix, cell_W_pix, W_cells, H_cells, new_img, cell_H_m, cell_W_m);
}

// ---------------------------------------------------------------------------
void Board::show() const {
    if (img.is_loaded()) {
        const_cast<Img&>(img).show();
    }
    // else: intentionally no-op – mirrors Python headless behaviour
}

// ---------------------------------------------------------------------------
std::pair<int, int> Board::m_to_cell(const std::pair<float, float>& pos_m) const {
    float x_m = pos_m.first;
    float y_m = pos_m.second;
    int col = static_cast<int>(std::round(x_m / cell_W_m));
    int row = static_cast<int>(std::round(y_m / cell_H_m));
    return {row, col};
}

std::pair<float, float> Board::cell_to_m(const std::pair<int, int>& cell) const {
    int r = cell.first;
    int c = cell.second;
    return {static_cast<float>(c) * cell_W_m, static_cast<float>(r) * cell_H_m};
}

std::pair<int, int> Board::m_to_pix(const std::pair<float, float>& pos_m) const {
    float x_m = pos_m.first;
    float y_m = pos_m.second;
    int x_px = static_cast<int>(std::round(x_m / cell_W_m * cell_W_pix));
    int y_px = static_cast<int>(std::round(y_m / cell_H_m * cell_H_pix));
    return {x_px, y_px};
} 