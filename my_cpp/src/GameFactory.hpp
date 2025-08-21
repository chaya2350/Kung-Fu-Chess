#pragma once
#include "Board.hpp"
#include "PieceFactory.hpp"
#include "Game.hpp"
#include <filesystem>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <memory>

static const int CELL_PX = 96;

inline std::shared_ptr<Game> create_game(const std::filesystem::path& pieces_root, std::function<Img(const std::filesystem::path&, std::pair<int, int>, bool)> img_factory) {
    try {
        auto board_csv = pieces_root / "board.csv";
        if (!std::filesystem::exists(board_csv)) {
            std::cerr << "[ERROR] File not found: " << board_csv << std::endl;
            throw std::runtime_error("File not found: " + board_csv.string());
        }
        auto board_png = pieces_root / "board.png";
        if (!std::filesystem::exists(board_png)) {
            std::cerr << "[ERROR] File not found: " << board_png << std::endl;
            throw std::runtime_error("File not found: " + board_png.string());
        }
        auto loader = img_factory;
        Img board_img = loader(board_png, {CELL_PX*8, CELL_PX*8}, false);
        Board board(CELL_PX, CELL_PX, 8, 8, board_img);
        auto gfx_factory = std::make_shared<GraphicsFactory>(img_factory);
        auto pf = std::make_shared<PieceFactory>(board, pieces_root, gfx_factory);
        std::vector<std::shared_ptr<Piece>> pieces;
        std::ifstream f(board_csv);
        std::string line;
        int r = 0;
        while (std::getline(f, line)) {
            std::istringstream iss(line);
            std::string code;
            int c = 0;
            while (std::getline(iss, code, ',')) {
                if (!code.empty()) {
                    
                    pieces.push_back(pf->create_piece(code, {r, c})); // r=שורה, c=עמודה
                }
                ++c;
            }
            ++r;
        }
        std::cout << "[DEBUG] create_game: all pieces created" << std::endl;
        return std::make_shared<Game>(pieces, board);
    } catch (const std::exception& ex) {
        std::cerr << "[EXCEPTION] in create_game: " << ex.what() << std::endl;
        throw;
    }
}
