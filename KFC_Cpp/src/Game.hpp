#pragma once

#include "Board.hpp"
#include "PieceFactory.hpp"
#include <memory>
#include <vector>
#include <stdexcept>
#include <filesystem>
#include <unordered_set>
#include "img/Img.hpp"
#include "img/ImgFactory.hpp"
#include <fstream>
#include <sstream>

class InvalidBoard : public std::runtime_error {
public:
    explicit InvalidBoard(const std::string& msg) : std::runtime_error(msg) {}
};

class Game {
public:
    Game(std::vector<std::shared_ptr<Piece>> pcs, Board board)
        : pieces(std::move(pcs)), board(std::move(board)) {
        validate();
    }

    std::vector<std::shared_ptr<Piece>> pieces;
    Board board;
private:
    void validate() {
        bool has_KW=false, has_KB=false;
        std::unordered_set<std::pair<int,int>, PairHash> seen;
        for(const auto& p: pieces) {
            if(p->id.rfind("KW",0) == 0) has_KW=true;
            if(p->id.rfind("KB",0) == 0) has_KB=true;
            auto cell = p->current_cell();
            if(!seen.insert(cell).second) throw InvalidBoard("Duplicate cell");
        }
        if(!has_KW || !has_KB) throw InvalidBoard("Missing kings");
    }
};

// ---------------------------------------------------------------------------
// Helper to read board.csv and create a full game --------------------------------
// ---------------------------------------------------------------------------
inline Game create_game(const std::string& pieces_root,
                        const std::shared_ptr<ImgFactory>& img_factory) {
    GraphicsFactory gfx_factory(img_factory);
    namespace fs = std::filesystem;
    fs::path root = std::filesystem::absolute(fs::path(pieces_root));
    fs::path board_csv = root / "board.csv";
    std::ifstream in(board_csv);
    if(!in) throw std::runtime_error("Cannot open board.csv");

    Board board(32,32,8,8, Img());
    PieceFactory pf(board, pieces_root, gfx_factory);
    std::vector<std::shared_ptr<Piece>> out;

    std::string line; int row=0;
    while(std::getline(in,line)) {
        std::stringstream ss(line);
        std::string cell; int col=0;
        while(std::getline(ss,cell,',')) {
            if(!cell.empty()) {
                auto piece = pf.create_piece(cell, {row,col});
                out.push_back(piece);
            }
            ++col;
        }
        ++row;
    }
    return Game(std::move(out), board);
} 