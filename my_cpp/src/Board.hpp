#include <utility>
#include <algorithm>
#include <iostream>

using std::pair;
using std::make_pair;
using std::round;
#pragma once
#include "Img.hpp"
#include <memory>
class Piece;
#include <cmath>
#include <utility>
#include <algorithm>
#include <iostream>

class Board {
public:
    int cell_H_pix; // cell height in pixels
    int cell_W_pix; // cell width in pixels
    int W_cells;    // num cells in width
    int H_cells;    // num cells in height
    Img img;        // image of the board
    float cell_H_m; // cell height in meters
    float cell_W_m; // cell width in meters
    std::vector<std::vector<std::shared_ptr<Piece>>> grid; // לוח הכלים

    Board(int cell_H_pix_, int cell_W_pix_, int W_cells_, int H_cells_, const Img& img_, float cell_H_m_ = 1.0f, float cell_W_m_ = 1.0f)
        : cell_H_pix(cell_H_pix_), cell_W_pix(cell_W_pix_), W_cells(W_cells_), H_cells(H_cells_), img(img_), cell_H_m(cell_H_m_), cell_W_m(cell_W_m_) {
    }
    Board() : cell_H_pix(0), cell_W_pix(0), W_cells(0), H_cells(0), img(), cell_H_m(1.0f), cell_W_m(1.0f) {
    }

    Board clone() const {
        return Board(cell_H_pix, cell_W_pix, W_cells, H_cells, img.copy(), cell_H_m, cell_W_m);
    }

    void show() {
        img.show();
    }


    pair<int, int> m_to_cell(const pair<float, float>& pos_m) const {
        float x_m = pos_m.first;
        float y_m = pos_m.second;
        int col = static_cast<int>(round(x_m / cell_W_m));
        int row = static_cast<int>(round(y_m / cell_H_m));
        return make_pair(row, col);
    }


    pair<float, float> cell_to_m(const pair<int, int>& cell) const {
        int r = cell.first;
        int c = cell.second;
        return make_pair(c * cell_W_m, r * cell_H_m);
    }

    pair<int, int> m_to_pix(const pair<float, float>& pos_m) const {
        float row = pos_m.first;  // שורה (0-7)
        float col = pos_m.second; // עמודה (0-7)
        int x_px = static_cast<int>(round(col * 96)); // עמודה -> X (שמאל-ימין)
        int y_px = static_cast<int>(round(row * 96)); // שורה -> Y (מעלה-מטה)
        return make_pair(x_px, y_px);
    }
};
