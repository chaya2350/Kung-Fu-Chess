#pragma once
#include "../../my_cpp_pub/GameLog.hpp"
#include "../../my_cpp_pub/Publisher.hpp"
#include "../../my_cpp_pub/Score.hpp"
#include "Board.hpp"
#include "Command.hpp"
#include "KeyboardInput.hpp"
#include "Piece.hpp"
#include "Sound.hpp"
#include <algorithm>
#include <chrono>
#include <iostream>
#include <map>
#include <memory>
#include <opencv2/opencv.hpp>
#include <queue>
#include <string>
#include <thread>
#include <vector>


class InvalidBoard : public std::exception {
public:
  const char *what() const noexcept override {
    return "Invalid board: missing kings";
  }
};


class Game {
public:
  std::vector<std::shared_ptr<Piece>> pieces;
  Board board;
  int64_t START_NS;
  int _time_factor;
  std::queue<Command> user_input_queue;
  std::map<std::pair<int, int>, std::vector<std::shared_ptr<Piece>>> pos;
  std::map<std::string, std::shared_ptr<Piece>> piece_by_id;
  std::string selected_id_1, selected_id_2;
  std::pair<int, int> last_cursor1, last_cursor2;
  std::unique_ptr<KeyboardProcessor> kp1, kp2;
  std::unique_ptr<KeyboardProducer> kb_prod_1, kb_prod_2;
  std::unique_ptr<Sound> sound;
  int board_size_px;
  int side_panel_width;
  int expanded_width;
  cv::Mat expanded_board_img;
  Board curr_board;

  // Publisher, Score, GameLog (from my_cpp_pub)
  Publisher publisher;
  Score score_white = Score("white", &publisher);
  Score score_black = Score("black", &publisher);
  GameLog game_log_white = GameLog("white", &publisher);
  GameLog game_log_black = GameLog("black", &publisher);

  Game(const std::vector<std::shared_ptr<Piece>> &pieces_, const Board &board_);

  int64_t game_time_ms() const;
  Board clone_board() const;
  void start_user_input_thread();
  void _update_cell2piece_map();
  void _run_game_loop(int num_iterations = -1, bool is_with_graphics = true);
  void run(int num_iterations = -1, bool is_with_graphics = true);
  void _draw();
  void _show();
  void _add_side_labels(cv::Mat &img);
  void _draw_valid_moves();
  void _check_pawn_promotion();
  std::vector<std::pair<int, int>> get_valid_moves(const std::string &piece_id);

  void _resolve_collisions();
  void _process_input(const Command &cmd);

  bool _validate(const std::vector<std::shared_ptr<Piece>> &pieces_) const;
  bool _is_win() const;
  void _announce_win();
};

