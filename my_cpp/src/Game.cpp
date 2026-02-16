// Required includes for Game class implementation
#include "Game.hpp"
#include <opencv2/opencv.hpp>
#include <iostream>
#include <cstdint>
#include <thread>
#include <chrono>
#include <fstream>

// Stub implementations to resolve linker errors (must come after includes)
void Game::_add_side_labels(cv::Mat&) {}
void Game::_draw_valid_moves() {}
void Game::_check_pawn_promotion() {}

void Game::_draw() {
    try {
        curr_board = clone_board();
        if (curr_board.img.img.empty()) {
            std::cout << "ERROR: cloned board image is empty!" << std::endl;
            return;
        }
        for (auto &p : pieces) {
            if (!p || !p->state || !p->state->physics) continue;
            
            // בדיקת תקינות פוינטר physics
            void* physics_ptr = p->state->physics.get();
            uintptr_t ptr_val = reinterpret_cast<uintptr_t>(physics_ptr);
            if (ptr_val == 0xDDDDDDDDDDDDDDDD || ptr_val == 0 || ptr_val < 0x1000) {
                continue; // דילוג על כלים פגומים
            }
            
            try {
                p->draw_on_board(curr_board, game_time_ms());
            } catch (...) {
                // שגיאה בציור - מדלגים
            }
        }
    } catch (const std::exception& e) {
        std::cout << "Error in _draw - board cloning failed: " << e.what() << std::endl;
        return;
    } catch (...) {
        std::cout << "Unknown error in _draw - board cloning failed" << std::endl;
        return;
    }
    try {
        // Create expanded image
        expanded_board_img = cv::Mat::zeros(board_size_px, expanded_width, CV_8UC3);
        // Left panel (white) - green
        expanded_board_img(cv::Rect(0, 0, side_panel_width, board_size_px)) = cv::Scalar(50, 150, 50);
        // Right panel (black) - blue
        expanded_board_img(cv::Rect(side_panel_width + board_size_px, 0, side_panel_width, board_size_px)) = cv::Scalar(150, 50, 50);

        // Convert board to BGR if needed
        cv::Mat board_img = curr_board.img.img;
        if (!board_img.empty()) {
            if (board_img.channels() == 4) {
                cv::cvtColor(board_img, board_img, cv::COLOR_BGRA2BGR);
            }
            board_img.copyTo(expanded_board_img(cv::Rect(side_panel_width, 0, board_size_px, board_size_px)));
        }
    } catch (...) {
        std::cout << "Error creating expanded board image" << std::endl;
        return;
    }

    _add_side_labels(expanded_board_img);
    _draw_valid_moves();

    // Draw cursors for both players
    if (kp1) {
        int r = last_cursor1.first, c = last_cursor1.second;
        int y1 = r * (board_size_px / 8);
        int x1 = c * (board_size_px / 8) + side_panel_width;
        int y2 = y1 + (board_size_px / 8) - 1;
        int x2 = x1 + (board_size_px / 8) - 1;
        cv::rectangle(expanded_board_img, cv::Point(x1, y1), cv::Point(x2, y2), cv::Scalar(0, 255, 0), 2);
    }
    if (kp2) {
        int r = last_cursor2.first, c = last_cursor2.second;
        int y1 = r * (board_size_px / 8);
        int x1 = c * (board_size_px / 8) + side_panel_width;
        int y2 = y1 + (board_size_px / 8) - 1;
        int x2 = x1 + (board_size_px / 8) - 1;
        cv::rectangle(expanded_board_img, cv::Point(x1, y1), cv::Point(x2, y2), cv::Scalar(255, 0, 0), 2);
    }
}

void Game::_show() {
    if (expanded_board_img.empty()) {
        std::cout << "ERROR: Board image is empty!" << std::endl;
        return;
    }
    
    try {
        cv::imshow("Chess Game", expanded_board_img);
        cv::moveWindow("Chess Game", 100, 100);
        
        int key = cv::waitKeyEx(30);
        if (key == 27) {
            exit(0);
        }
    } catch (const cv::Exception& e) {
        std::cout << "OpenCV error in _show: " << e.what() << std::endl;
    } catch (...) {
        std::cout << "Unknown error in _show" << std::endl;
    }
}

void Game::_resolve_collisions() {
    _update_cell2piece_map();
    _check_pawn_promotion();
    int pieces_before = pieces.size();
    for (auto &entry : pos) {
        auto &plist = entry.second;
        if (plist.size() < 2)
            continue;
        // Advanced collision logic: knight/moving piece priority
        std::vector<std::shared_ptr<Piece>> knights_moving, other_pieces, moving_pieces, stationary_pieces;
        for (auto &p : plist) {
            if ((p->id.substr(0, 2) == "NW" || p->id.substr(0, 2) == "NB") && p->state && p->state->name == "move")
                knights_moving.push_back(p);
            else
                other_pieces.push_back(p);
        }
        std::shared_ptr<Piece> winner;
        if (!knights_moving.empty()) {
            auto knight = knights_moving[0];
            if (knight->state && knight->state->physics) {
                auto dest = knight->state->physics->_end_cell;
                auto curr = knight->current_cell();
                if (curr != std::make_pair(dest[0], dest[1]))
                    continue;
            }
            winner = knight;
        } else {
            for (auto &p : plist) {
                if (p->state && p->state->name != "idle")
                    moving_pieces.push_back(p);
                else
                    stationary_pieces.push_back(p);
            }
            if (!moving_pieces.empty()) {
                winner = *std::max_element(moving_pieces.begin(), moving_pieces.end(), [](const std::shared_ptr<Piece>& a, const std::shared_ptr<Piece>& b) {
                    return a->state->physics->get_start_ms() < b->state->physics->get_start_ms();
                });
            } else {
                winner = *std::max_element(plist.begin(), plist.end(), [](const std::shared_ptr<Piece>& a, const std::shared_ptr<Piece>& b) {
                    return a->state->physics->get_start_ms() < b->state->physics->get_start_ms();
                });
            }
        }
        for (auto &p : plist) {
            if (p == winner) continue;
            if (p->state && p->state->can_be_captured()) {
                if (p->id.substr(0, 2) == "KW") {
                    game_log_white.add("Captured: " + p->id);
                    score_black.add(1);
                } else if (p->id.substr(0, 2) == "KB") {
                    game_log_black.add("Captured: " + p->id);
                    score_white.add(1);
                } else if (p->id[1] == 'W') {
                    game_log_white.add("Captured: " + p->id);
                    score_black.add(1);
                } else if (p->id[1] == 'B') {
                    game_log_black.add("Captured: " + p->id);
                    score_white.add(1);
                }
                if (sound) sound->play("../../sounds/Boom_sound.wav");
                auto it = std::find(pieces.begin(), pieces.end(), p);
                if (it != pieces.end()) pieces.erase(it);
            }
        }
        plist.clear();
        plist.push_back(winner);
    }
    int pieces_after = pieces.size();
    if (pieces_before != pieces_after) {
    }
}

bool Game::_validate(const std::vector<std::shared_ptr<Piece>> &pieces_) const {
    bool has_white_king = false, has_black_king = false;
    std::map<std::pair<int, int>, std::string> seen_cells;
    for (const auto &p : pieces_) {
        auto cell = p->current_cell();
        std::string piece_color(1, p->id[1]);
        if (seen_cells.count(cell)) {
            if (seen_cells[cell] == piece_color)
                return false;
        } else {
            seen_cells[cell] = piece_color;
        }
        if (p->id.substr(0, 2) == "KW")
            has_white_king = true;
        else if (p->id.substr(0, 2) == "KB")
            has_black_king = true;
    }
    return has_white_king && has_black_king;
}

bool Game::_is_win() const {
    // בדיקה אם יש שני מלכים
    bool has_white_king = false;
    bool has_black_king = false;
    
    for (const auto &p : pieces) {
        if (!p) continue;
        if (p->id.substr(0, 2) == "KW") has_white_king = true;
        if (p->id.substr(0, 2) == "KB") has_black_king = true;
    }
    
    return !has_white_king || !has_black_king; // משחק מסתיים אם אין אחד מהמלכים
}

void Game::_announce_win() {
    if (!sound) sound = std::make_unique<Sound>();
    sound->play("../../sounds/applause.wav");
    
    // בדיקה מי ניצח לפי אילו מלכים נשארו
    bool has_white_king = false;
    bool has_black_king = false;
    
    for (const auto &p : pieces) {
        if (!p) continue;
        if (p->id.substr(0, 2) == "KW") has_white_king = true;
        if (p->id.substr(0, 2) == "KB") has_black_king = true;
    }
    
    bool black_win = has_black_king && !has_white_king;
    std::string win_text = black_win ? "Black wins!" : "White wins!";
    
    if (black_win) {
        game_log_black.add(win_text);
        score_black.add(10);
    } else {
        game_log_white.add(win_text);
        score_white.add(10);
    }
    
    // הצגת תמונת ניצחון רק על חלק הלוח
    std::string img_path = black_win ? "../../pic/black_win.png" : "../../pic/white_win.png";
    cv::Mat victory_img = cv::imread(img_path);
    if (!victory_img.empty() && !expanded_board_img.empty()) {
        // שינוי גודל התמונה לגודל הלוח בלבד
        cv::resize(victory_img, victory_img, cv::Size(board_size_px, board_size_px));
        // העתקת התמונה רק על חלק הלוח (השארת הצדדים)
        victory_img.copyTo(expanded_board_img(cv::Rect(side_panel_width, 0, board_size_px, board_size_px)));
        cv::imshow("Chess Game", expanded_board_img);
        cv::waitKey(5000); // הצגה ל-5 שניות
    } else {
        std::cout << "Could not load victory image: " << img_path << std::endl;
    }
    
    std::cout << win_text << std::endl;
}
#include "Game.hpp"


Game::Game(const std::vector<std::shared_ptr<Piece>> &pieces_, const Board &board_)
    : pieces(pieces_), board(board_), _time_factor(1), board_size_px(768),
      side_panel_width(300),
      expanded_width(board_size_px + 2 * side_panel_width) {
  if (!_validate(pieces_))
    throw InvalidBoard();
  START_NS = std::chrono::steady_clock::now().time_since_epoch().count();
  for (const auto &p : pieces)
    piece_by_id[p->id] = p;
  sound = std::make_unique<Sound>();
  // Initialize keyboard processors and producers (stub)
  kp1 = std::make_unique<KeyboardProcessor>(8, 8, std::map<std::string, std::string>{{"up","up"},{"down","down"},{"left","left"},{"right","right"}});
  kp2 = std::make_unique<KeyboardProcessor>(8, 8, std::map<std::string, std::string>{{"w","up"},{"s","down"},{"a","left"},{"d","right"}});
  kb_prod_1 = std::make_unique<KeyboardProducer>(kp1.get(), &user_input_queue, 1);
  kb_prod_2 = std::make_unique<KeyboardProducer>(kp2.get(), &user_input_queue, 2);
  last_cursor1 = kp1->get_cursor();
  last_cursor2 = kp2->get_cursor();
}

int64_t Game::game_time_ms() const {
  int64_t now_ns =
      std::chrono::steady_clock::now().time_since_epoch().count();
  return _time_factor * (now_ns - START_NS) / 1000000;
}

Board Game::clone_board() const { return board.clone(); }

void Game::start_user_input_thread() {
  // Start keyboard input threads (stub)
  if (kb_prod_1) kb_prod_1->start();
  if (kb_prod_2) kb_prod_2->start();
}

void Game::_update_cell2piece_map() {
  pos.clear();
  for (const auto &p : pieces) {
      if (!p || !p->state || !p->state->physics) continue;
      
      // בדיקת תקינות פוינטר physics
      void* physics_ptr = p->state->physics.get();
      uintptr_t ptr_val = reinterpret_cast<uintptr_t>(physics_ptr);
      if (ptr_val == 0xDDDDDDDDDDDDDDDD || ptr_val == 0 || ptr_val < 0x1000) {
          continue; // דילוג על כלים פגומים
      }
      
      try {
          auto cell = p->current_cell();
          pos[cell].push_back(p);
      } catch (...) {
          // שגיאה - מדלגים
      }
  }
}

void Game::_run_game_loop(int num_iterations, bool is_with_graphics) {
  int it_counter = 0;
  std::cout << "Starting chess game..." << std::endl;
  // אתחול מצביעים - שחקן 1 על כלים שחורים, שחקן 2 על כלים לבנים
  last_cursor1 = {0, 0}; // שחקן 1 - כלים שחורים
  last_cursor2 = {7, 0}; // שחקן 2 - כלים לבנים
  
  // משתנים לעקוב אחרי כלים נבחרים
  std::pair<int,int> selected_piece1 = {-1, -1};
  std::pair<int,int> selected_piece2 = {-1, -1};
  
  // דגלים למנוע לחיצות כפולות
  static bool space_pressed = false;
  static bool enter_pressed = false;
  
  // משתנים לאנימציה
  struct MovingPiece {
    std::shared_ptr<Piece> piece;
    std::pair<float,float> start_pos;
    std::pair<float,float> end_pos;
    int start_time;
    int duration = 300; // 0.3 שנייה
  };
  std::vector<MovingPiece> moving_pieces;
  
  // מעקב אחרי מצבי כלים לאנימציה
  std::map<std::string, std::string> piece_states; // piece_id -> state_name
  std::map<std::string, int> piece_state_start_time; // piece_id -> start_time
  
  // פונקציה לבדיקת חוקיות התנועה
  auto is_valid_move = [&](std::shared_ptr<Piece> piece, std::pair<int,int> from, std::pair<int,int> to) -> bool {
    if (!piece || !piece->state) return false;
    
    // חישוב ההפרש
    int dr = to.first - from.first;
    int dc = to.second - from.second;
    
    // קריאת קובץ moves.txt
    std::string piece_type = piece->id.substr(0, 2);
    std::string moves_file = "../../pieces/" + piece_type + "/states/idle/moves.txt";
    
    std::ifstream file(moves_file);
    if (!file.is_open()) {
      std::cout << "Cannot open moves file: " << moves_file << " for piece " << piece->id << std::endl;
      // אם אין קובץ moves - נתיר כל תנועה (לעת)
      return true;
    }
    
    std::string line;
    while (std::getline(file, line)) {
      if (line.empty()) continue;
      
      // טיפול בשני פורמטים: "dr,dc:type" או "dr,dc"
      size_t colon_pos = line.find(':');
      std::string move_part;
      
      if (colon_pos != std::string::npos) {
        // פורמט עם סוג: "dr,dc:type"
        move_part = line.substr(0, colon_pos);
      } else {
        // פורמט פשוט: "dr,dc"
        move_part = line;
      }
      
      size_t comma_pos = move_part.find(',');
      if (comma_pos == std::string::npos) continue;
      
      try {
        int file_dr = std::stoi(move_part.substr(0, comma_pos));
        int file_dc = std::stoi(move_part.substr(comma_pos + 1));
        
        if (file_dr == dr && file_dc == dc) {
          return true;
        }
      } catch (...) {
        // שגיאה בפירוק - מדלגים
        continue;
      }
    }
    
    return false;
  };
  try {
    while (!_is_win() && (num_iterations <= 0 || it_counter < num_iterations)) {
      // ללא עדכון כלים - רק אנימציות חזותיות
      
      while (!user_input_queue.empty()) {
        Command cmd = user_input_queue.front();
        user_input_queue.pop();
        _process_input(cmd);
      }
      
      if (is_with_graphics) {
        try {
          expanded_board_img = cv::Mat::zeros(board_size_px, expanded_width, CV_8UC3);
          expanded_board_img(cv::Rect(0, 0, side_panel_width, board_size_px)) = cv::Scalar(50, 150, 50);
          expanded_board_img(cv::Rect(side_panel_width + board_size_px, 0, side_panel_width, board_size_px)) = cv::Scalar(150, 50, 50);
          cv::Mat chess_board = cv::Mat::zeros(board_size_px, board_size_px, CV_8UC3);
          int square_size = board_size_px / 8;
          for (int r = 0; r < 8; r++) {
            for (int c = 0; c < 8; c++) {
              cv::Scalar color = ((r + c) % 2 == 0) ? cv::Scalar(240, 217, 181) : cv::Scalar(181, 136, 99);
              cv::rectangle(chess_board, cv::Point(c * square_size, r * square_size), 
                           cv::Point((c + 1) * square_size, (r + 1) * square_size), color, -1);
            }
          }
          chess_board.copyTo(expanded_board_img(cv::Rect(side_panel_width, 0, board_size_px, board_size_px)));
          
          // ציור הכלים על הלוח
          for (const auto &p : pieces) {
            if (!p || !p->state || !p->state->physics) continue;
            try {
              // שימוש ישיר במיקום הפיזיקלי במקום current_cell()
              int row, col;
              if (p->state && p->state->physics) {
                row = static_cast<int>(p->state->physics->_curr_pos_m[0]);
                col = static_cast<int>(p->state->physics->_curr_pos_m[1]);
                
                // Debug - הדפסה רק לכלי שזז
                if (p->id == "PB_1,0" || p->id == "PB_1,1") {
                  std::cout << "Drawing " << p->id << " at physics pos (" << row << "," << col << ")" << std::endl;
                }
              } else {
                auto cell = p->current_cell();
                row = cell.first;
                col = cell.second;
              }
              
              if (row >= 0 && row < 8 && col >= 0 && col < 8) {
                int x = side_panel_width + col * square_size;
                int y = row * square_size;
                
                // בניית שם קובץ התמונה לפי מצב הכלי
                std::string piece_type = p->id.substr(0, 2);
                std::string state_name = "idle";
                
                // בדיקת מצב הכלי מהמעקב שלנו
                if (piece_states.count(p->id)) {
                  int elapsed = game_time_ms() - piece_state_start_time[p->id];
                  if (piece_states[p->id] == "move" && elapsed < 1000) {
                    state_name = "move";
                  } else if (piece_states[p->id] == "move" && elapsed >= 1000 && elapsed < 3000) {
                    state_name = "long_rest";
                  } else if (elapsed >= 3000) {
                    piece_states[p->id] = "idle"; // חזרה ל-idle
                  }
                }
                
                // חישוב מספר התמונה (מתחלף בין 1-5)
                int frame = ((game_time_ms() / 200) % 5) + 1; // החלפה כל 200ms
                
                std::string piece_file = "../../pieces/" + piece_type + "/states/" + state_name + "/sprites/" + std::to_string(frame) + ".png";
                cv::Mat piece_img = cv::imread(piece_file, cv::IMREAD_UNCHANGED);
                
                // Debug - בדיקה ראשונה בלבד
                static bool first_check = true;
                if (first_check) {
                  std::cout << "Trying to load: " << piece_file << std::endl;
                  std::cout << "Image loaded: " << (!piece_img.empty() ? "YES" : "NO") << std::endl;
                  first_check = false;
                }
                
                if (!piece_img.empty()) {
                  // שינוי גודל התמונה לגודל המשבצת
                  cv::Mat resized_piece;
                  cv::resize(piece_img, resized_piece, cv::Size(square_size, square_size));
                  
                  // טיפול בשקיפות (alpha channel)
                  if (resized_piece.channels() == 4) {
                    std::vector<cv::Mat> channels;
                    cv::split(resized_piece, channels);
                    cv::Mat alpha = channels[3];
                    cv::Mat bgr;
                    cv::merge(std::vector<cv::Mat>{channels[0], channels[1], channels[2]}, bgr);
                    
                    // העתקת התמונה עם שקיפות
                    cv::Mat roi = expanded_board_img(cv::Rect(x, y, square_size, square_size));
                    for (int i = 0; i < bgr.rows; ++i) {
                      for (int j = 0; j < bgr.cols; ++j) {
                        if (alpha.at<uchar>(i, j) > 128) {
                          roi.at<cv::Vec3b>(i, j) = bgr.at<cv::Vec3b>(i, j);
                        }
                      }
                    }
                  } else {
                    // העתקה רגילה ללא שקיפות
                    resized_piece.copyTo(expanded_board_img(cv::Rect(x, y, square_size, square_size)));
                  }
                } else {
                  // אם אין תמונה - ציור עיגול פשוט
                  cv::Scalar piece_color = (p->id[1] == 'W') ? cv::Scalar(255, 255, 255) : cv::Scalar(0, 0, 0);
                  cv::circle(expanded_board_img, cv::Point(x + square_size/2, y + square_size/2), 
                            square_size/4, piece_color, -1);
                  cv::circle(expanded_board_img, cv::Point(x + square_size/2, y + square_size/2), 
                            square_size/4, cv::Scalar(128, 128, 128), 2);
                }
              }
            } catch (...) {
              // שגיאה בציור כלי - מדלגים
            }
          }
          
          // ציור כלים נבחרים
          if (selected_piece1.first != -1) {
            int r = selected_piece1.first, c = selected_piece1.second;
            int y1 = r * square_size;
            int x1 = c * square_size + side_panel_width;
            int y2 = y1 + square_size - 1;
            int x2 = x1 + square_size - 1;
            cv::rectangle(expanded_board_img, cv::Point(x1, y1), cv::Point(x2, y2), cv::Scalar(0, 255, 255), 4); // צהוב
          }
          if (selected_piece2.first != -1) {
            int r = selected_piece2.first, c = selected_piece2.second;
            int y1 = r * square_size;
            int x1 = c * square_size + side_panel_width;
            int y2 = y1 + square_size - 1;
            int x2 = x1 + square_size - 1;
            cv::rectangle(expanded_board_img, cv::Point(x1, y1), cv::Point(x2, y2), cv::Scalar(255, 255, 0), 4); // ציאן
          }
          
          // ציור מצביעים
          int r1 = last_cursor1.first, c1 = last_cursor1.second;
          int y1 = r1 * square_size;
          int x1 = c1 * square_size + side_panel_width;
          int y2 = y1 + square_size - 1;
          int x2 = x1 + square_size - 1;
          cv::rectangle(expanded_board_img, cv::Point(x1, y1), cv::Point(x2, y2), cv::Scalar(0, 255, 0), 3);
          
          int r2 = last_cursor2.first, c2 = last_cursor2.second;
          y1 = r2 * square_size;
          x1 = c2 * square_size + side_panel_width;
          y2 = y1 + square_size - 1;
          x2 = x1 + square_size - 1;
          cv::rectangle(expanded_board_img, cv::Point(x1, y1), cv::Point(x2, y2), cv::Scalar(255, 0, 0), 3);
          
          // ציור ניקוד ומידע שחקנים
          // צד שמאל - שחקן שחור
          cv::putText(expanded_board_img, "BLACK PLAYER", cv::Point(10, 30), cv::FONT_HERSHEY_SIMPLEX, 0.7, cv::Scalar(255, 255, 255), 2);
          cv::putText(expanded_board_img, "Score: " + std::to_string(score_black.get_score()), cv::Point(10, 60), cv::FONT_HERSHEY_SIMPLEX, 0.6, cv::Scalar(0, 255, 0), 2);
          cv::putText(expanded_board_img, "Controls: WASD + Space", cv::Point(10, 90), cv::FONT_HERSHEY_SIMPLEX, 0.4, cv::Scalar(200, 200, 200), 1);
          
          // הצגת לוגים שחורים
          cv::putText(expanded_board_img, "Recent Moves:", cv::Point(10, 130), cv::FONT_HERSHEY_SIMPLEX, 0.5, cv::Scalar(255, 255, 0), 1);
          static std::vector<std::string> black_moves_log;
          // שמירת המהלכים במשתנה סטטי
          
          // צד ימין - שחקן לבן
          int right_x = side_panel_width + board_size_px + 10;
          cv::putText(expanded_board_img, "WHITE PLAYER", cv::Point(right_x, 30), cv::FONT_HERSHEY_SIMPLEX, 0.7, cv::Scalar(255, 255, 255), 2);
          cv::putText(expanded_board_img, "Score: " + std::to_string(score_white.get_score()), cv::Point(right_x, 60), cv::FONT_HERSHEY_SIMPLEX, 0.6, cv::Scalar(0, 255, 0), 2);
          cv::putText(expanded_board_img, "Controls: -> <- ... + Enter", cv::Point(right_x, 90), cv::FONT_HERSHEY_SIMPLEX, 0.4, cv::Scalar(200, 200, 200), 1);
          
          // הצגת לוגים לבנים
          cv::putText(expanded_board_img, "Recent Moves:", cv::Point(right_x, 130), cv::FONT_HERSHEY_SIMPLEX, 0.5, cv::Scalar(255, 255, 0), 1);
          static std::vector<std::string> white_moves_log;
          
          // ציור לוגים שחורים
          for (size_t i = 0; i < black_moves_log.size() && i < 8; ++i) {
            std::string display_move = black_moves_log[i];
            if (display_move.length() > 25) display_move = display_move.substr(0, 22) + "...";
            cv::putText(expanded_board_img, display_move, cv::Point(10, 160 + i * 20), 
                       cv::FONT_HERSHEY_SIMPLEX, 0.35, cv::Scalar(200, 200, 200), 1);
          }
          
          // ציור לוגים לבנים
          for (size_t i = 0; i < white_moves_log.size() && i < 8; ++i) {
            std::string display_move = white_moves_log[i];
            if (display_move.length() > 25) display_move = display_move.substr(0, 22) + "...";
            cv::putText(expanded_board_img, display_move, cv::Point(right_x, 160 + i * 20), 
                       cv::FONT_HERSHEY_SIMPLEX, 0.35, cv::Scalar(200, 200, 200), 1);
          }
          
          cv::imshow("Chess Game", expanded_board_img);
          int key = cv::waitKeyEx(30);
          if (key == 27) exit(0);
          
          // ללא debug מקשים
          
          // שליטה במצביעים - WASD לשחקן 1 (ירוק - כלים שחורים)
          if ((key == 119 || key == 87) && last_cursor1.first > 0) {
            last_cursor1.first--;
          }
          if ((key == 115 || key == 83) && last_cursor1.first < 7) {
            last_cursor1.first++;
          }
          if ((key == 97 || key == 65) && last_cursor1.second > 0) {
            last_cursor1.second--;
          }
          if ((key == 100 || key == 68) && last_cursor1.second < 7) {
            last_cursor1.second++;
          }
          
          // חיצים לשחקן 2 (אדום - כלים לבנים)
          if (key == 2490368 && last_cursor2.first > 0) { // חץ למעלה
            last_cursor2.first--;
          }
          if (key == 2621440 && last_cursor2.first < 7) { // חץ למטה
            last_cursor2.first++;
          }
          if (key == 2424832 && last_cursor2.second > 0) { // חץ שמאלה
            last_cursor2.second--;
          }
          if (key == 2555904 && last_cursor2.second < 7) { // חץ ימינה
            last_cursor2.second++;
          }
          
          // בחירת כלים
          if (key == 32 && !space_pressed) { // רווח - שחקן 1
            space_pressed = true;
            if (selected_piece1.first == -1) {
              // חיפוש איזה כלי במיקום הזה ובדיקת מצבו
              std::string piece_at_pos = "None";
              bool can_select = false;
              for (const auto &p : pieces) {
                if (p && p->current_cell() == last_cursor1) {
                  piece_at_pos = p->id;
                  // בדיקה אם הכלי במצב שניתן לבחור בו
                  std::string current_state = "idle";
                  if (piece_states.count(p->id)) {
                    int elapsed = game_time_ms() - piece_state_start_time[p->id];
                    if (piece_states[p->id] == "move" && elapsed < 1000) {
                      current_state = "move";
                    } else if (piece_states[p->id] == "move" && elapsed >= 1000 && elapsed < 3000) {
                      current_state = "long_rest";
                    }
                  }
                  
                  if (current_state == "move" || current_state == "long_rest") {
                    std::cout << "[WARN] Cannot select " << p->id << " - piece is busy (" << current_state << ")" << std::endl;
                    can_select = false;
                  } else {
                    can_select = true;
                  }
                  break;
                }
              }
              
              if (can_select) {
                selected_piece1 = last_cursor1;
                std::cout << "Player 1 selected piece at (" << last_cursor1.first << "," << last_cursor1.second << ") - piece: " << piece_at_pos << std::endl;
              }
            } else {
              std::cout << "Player 1 moving piece from (" << selected_piece1.first << "," << selected_piece1.second << ") to (" << last_cursor1.first << "," << last_cursor1.second << ")" << std::endl;
              // חיפוש הכלי ובדיקת חוקיות
              std::cout << "Looking for piece at (" << selected_piece1.first << "," << selected_piece1.second << ")" << std::endl;
              for (auto &p : pieces) {
                if (p) {
                  auto current_pos = p->current_cell();
                  std::cout << "Found piece " << p->id << " at (" << current_pos.first << "," << current_pos.second << ")" << std::endl;
                }
                if (p && p->current_cell() == selected_piece1) {
                  std::cout << "MATCH! Found piece " << p->id << " for movement" << std::endl;
                  // בדיקת חוקיות התנועה
                  std::cout << "Checking if move is valid..." << std::endl;
                  bool move_valid = is_valid_move(p, selected_piece1, {last_cursor1.first, last_cursor1.second});
                  std::cout << "Move valid: " << (move_valid ? "YES" : "NO") << std::endl;
                  if (move_valid) {
                    std::cout << "ENTERING MOVE EXECUTION" << std::endl;
                    // דילוג על on_command - עדכון ישיר של המיקום
                    std::cout << "Skipping on_command, updating position directly..." << std::endl;
                    
                    // עדכון מלא של מיקום הכלי
                    std::cout << "About to update piece position..." << std::endl;
                    if (p->state && p->state->physics) {
                      std::cout << "Physics exists, updating position from (" << p->state->physics->_curr_pos_m[0] << "," << p->state->physics->_curr_pos_m[1] << ") to (" << last_cursor1.first << "," << last_cursor1.second << ")" << std::endl;
                      p->state->physics->_curr_pos_m[0] = static_cast<float>(last_cursor1.first);
                      p->state->physics->_curr_pos_m[1] = static_cast<float>(last_cursor1.second);
                      p->state->physics->_start_cell[0] = last_cursor1.first;
                      p->state->physics->_start_cell[1] = last_cursor1.second;
                      p->state->physics->_end_cell[0] = last_cursor1.first;
                      p->state->physics->_end_cell[1] = last_cursor1.second;
                      std::cout << "Position updated! New physics pos: (" << p->state->physics->_curr_pos_m[0] << "," << p->state->physics->_curr_pos_m[1] << ")" << std::endl;
                    } else {
                      std::cout << "ERROR: No physics state available!" << std::endl;
                    }
                    
                    // עדכון מצב הכלי לאנימציה
                    piece_states[p->id] = "move";
                    piece_state_start_time[p->id] = game_time_ms();
                    
                    // בדיקת קידום חייל למלכה
                    if (p->id.substr(0, 2) == "PB" && last_cursor1.first == 7) {
                      p->id = "QB" + p->id.substr(2);
                      std::cout << "Pawn promoted to Queen: " << p->id << std::endl;
                    } else if (p->id.substr(0, 2) == "PW" && last_cursor1.first == 0) {
                      p->id = "QW" + p->id.substr(2);
                      std::cout << "Pawn promoted to Queen: " << p->id << std::endl;
                    }
                    
                    // השמעת קול צעדים
                    if (sound) sound->play("../../sounds/foot_step.wav");
                    
                    // עדכון לוג (ללא ניקוד על מהלך רגיל)
                    std::string move_str = p->id + ": (" + std::to_string(selected_piece1.first) + "," + std::to_string(selected_piece1.second) + ") -> (" + std::to_string(last_cursor1.first) + "," + std::to_string(last_cursor1.second) + ")";
                    if (p->id[1] == 'B') {
                      game_log_black.add(move_str);
                      black_moves_log.push_back(move_str);
                      if (black_moves_log.size() > 8) black_moves_log.erase(black_moves_log.begin());
                    }
                    
                    // בדיקה אם יש כלי יריב במיקום היעד (אכילה)
                    for (auto it = pieces.begin(); it != pieces.end(); ++it) {
                      auto &enemy = *it;
                      if (enemy && enemy != p && enemy->current_cell() == std::make_pair(last_cursor1.first, last_cursor1.second) && enemy->id[1] != p->id[1]) {
                        game_log_black.add("Captured: " + enemy->id);
                        // השמעת קול אכילה
                        if (sound) sound->play("../../sounds/Boom_sound.wav");
                        
                        if (enemy->id.substr(0, 2) == "KW") {
                          score_black.add(100); // ניקוד מיוחד לאכילת מלך
                          game_log_black.add("CHECKMATE! Black wins!");
                        } else {
                          score_black.add(10); // ניקוד רגיל לאכילה
                        }
                        pieces.erase(it); // הסרת הכלי הנאכל
                        break;
                      }
                    }
                    std::cout << "Valid move - started animation" << std::endl;
                  } else {
                    std::cout << "Invalid move!" << std::endl;
                  }
                  break;
                }
              }
              selected_piece1 = {-1, -1}; // ביטול בחירה
            }
          } else if (key != 32) {
            space_pressed = false; // איפוס דגל כשמקש אחר נלחץ
          }
          if (key == 13) { // אנטר - שחקן 2
            if (selected_piece2.first == -1) {
              // חיפוש איזה כלי במיקום הזה ובדיקת מצבו
              std::string piece_at_pos = "None";
              bool can_select = false;
              for (const auto &p : pieces) {
                if (p && p->current_cell() == last_cursor2) {
                  piece_at_pos = p->id;
                  // בדיקה אם הכלי במצב שניתן לבחור בו
                  std::string current_state = "idle";
                  if (piece_states.count(p->id)) {
                    int elapsed = game_time_ms() - piece_state_start_time[p->id];
                    if (piece_states[p->id] == "move" && elapsed < 1000) {
                      current_state = "move";
                    } else if (piece_states[p->id] == "move" && elapsed >= 1000 && elapsed < 3000) {
                      current_state = "long_rest";
                    }
                  }
                  
                  if (current_state == "move" || current_state == "long_rest") {
                    std::cout << "[WARN] Cannot select " << p->id << " - piece is busy (" << current_state << ")" << std::endl;
                    can_select = false;
                  } else {
                    can_select = true;
                  }
                  break;
                }
              }
              
              if (can_select) {
                selected_piece2 = last_cursor2;
                std::cout << "Player 2 selected piece at (" << last_cursor2.first << "," << last_cursor2.second << ") - piece: " << piece_at_pos << std::endl;
              }
            } else {
              std::cout << "Player 2 moving piece from (" << selected_piece2.first << "," << selected_piece2.second << ") to (" << last_cursor2.first << "," << last_cursor2.second << ")" << std::endl;
              // חיפוש הכלי ובדיקת חוקיות
              for (auto &p : pieces) {
                if (p && p->current_cell() == selected_piece2) {
                  // בדיקת חוקיות התנועה
                  if (is_valid_move(p, selected_piece2, {last_cursor2.first, last_cursor2.second})) {
                    // דילוג על on_command - עדכון ישיר של המיקום
                    std::cout << "Player 2: Skipping on_command, updating position directly..." << std::endl;
                    
                    // עדכון מלא של מיקום הכלי
                    if (p->state && p->state->physics) {
                      p->state->physics->_curr_pos_m[0] = static_cast<float>(last_cursor2.first);
                      p->state->physics->_curr_pos_m[1] = static_cast<float>(last_cursor2.second);
                      p->state->physics->_start_cell[0] = last_cursor2.first;
                      p->state->physics->_start_cell[1] = last_cursor2.second;
                      p->state->physics->_end_cell[0] = last_cursor2.first;
                      p->state->physics->_end_cell[1] = last_cursor2.second;
                      std::cout << "Piece moved to (" << last_cursor2.first << "," << last_cursor2.second << ")" << std::endl;
                    }
                    
                    // עדכון מצב הכלי לאנימציה
                    piece_states[p->id] = "move";
                    piece_state_start_time[p->id] = game_time_ms();
                    
                    // בדיקת קידום חייל למלכה
                    if (p->id.substr(0, 2) == "PW" && last_cursor2.first == 0) {
                      p->id = "QW" + p->id.substr(2);
                      std::cout << "Pawn promoted to Queen: " << p->id << std::endl;
                    } else if (p->id.substr(0, 2) == "PB" && last_cursor2.first == 7) {
                      p->id = "QB" + p->id.substr(2);
                      std::cout << "Pawn promoted to Queen: " << p->id << std::endl;
                    }
                    
                    // השמעת קול צעדים
                    if (sound) sound->play("../../sounds/foot_step.wav");
                    
                    // עדכון לוג (ללא ניקוד על מהלך רגיל)
                    std::string move_str = p->id + ": (" + std::to_string(selected_piece2.first) + "," + std::to_string(selected_piece2.second) + ") -> (" + std::to_string(last_cursor2.first) + "," + std::to_string(last_cursor2.second) + ")";
                    if (p->id[1] == 'W') {
                      game_log_white.add(move_str);
                      white_moves_log.push_back(move_str);
                      if (white_moves_log.size() > 8) white_moves_log.erase(white_moves_log.begin());
                    }
                    
                    // בדיקה אם יש כלי יריב במיקום היעד (אכילה)
                    for (auto it = pieces.begin(); it != pieces.end(); ++it) {
                      auto &enemy = *it;
                      if (enemy && enemy != p && enemy->current_cell() == std::make_pair(last_cursor2.first, last_cursor2.second) && enemy->id[1] != p->id[1]) {
                        game_log_white.add("Captured: " + enemy->id);
                        // השמעת קול אכילה
                        if (sound) sound->play("../../sounds/Boom_sound.wav");
                        
                        if (enemy->id.substr(0, 2) == "KB") {
                          score_white.add(100); // ניקוד מיוחד לאכילת מלך
                          game_log_white.add("CHECKMATE! White wins!");
                        } else {
                          score_white.add(10); // ניקוד רגיל לאכילה
                        }
                        pieces.erase(it); // הסרת הכלי הנאכל
                        break;
                      }
                    }
                    std::cout << "Valid move - started animation" << std::endl;
                  } else {
                    std::cout << "Invalid move!" << std::endl;
                  }
                  break;
                }
              }
              selected_piece2 = {-1, -1}; // ביטול בחירה
            }
          }
        } catch (...) {
          // שגיאה בגרפיקה - ממשיכים
        }
      }
      
      ++it_counter;
      std::this_thread::sleep_for(std::chrono::milliseconds(16)); // ~60 FPS
      if (num_iterations > 0 && num_iterations <= it_counter) {
          return;
      }
    }
  } catch (const std::exception& e) {
    std::cout << "Exception in game loop: " << e.what() << std::endl;
  } catch (...) {
    std::cout << "Unknown exception in game loop" << std::endl;
  }
  if (_is_win()) {
    std::cout << "Game ended - win condition met after " << it_counter << " iterations" << std::endl;
  } else {
    std::cout << "Game loop ended after " << it_counter << " iterations" << std::endl;
  }
}

void Game::run(int num_iterations, bool is_with_graphics) {
  try {
    start_user_input_thread();
    for (auto &p : pieces)
      p->reset(START_NS);
    _run_game_loop(num_iterations, is_with_graphics);
    if (_is_win()) {
      _announce_win();
    }
    if (kb_prod_1) kb_prod_1->stop();
    if (kb_prod_2) kb_prod_2->stop();
  } catch (const std::exception &ex) {
    std::cerr << "[EXCEPTION] " << ex.what() << std::endl;
  } catch (...) {
    std::cerr << "[EXCEPTION] unknown exception" << std::endl;
  }
}



// Helper to convert Command to string for publishing
static std::string command_to_string(const Command& cmd) {
    std::string s = "type:" + cmd.type + ",piece_id:" + cmd.piece_id + ",params:";
    for (const auto& param : cmd.params) {
        // Try to print as pair<int,int> or fallback to typeid
        try {
            auto cell = std::any_cast<std::pair<int, int>>(param);
            s += "(" + std::to_string(cell.first) + "," + std::to_string(cell.second) + ") ";
        } catch (...) {
            s += std::string("[type:") + param.type().name() + "] ";
        }
    }
    return s;
}

void Game::_process_input(const Command &cmd) {
    auto it = piece_by_id.find(cmd.piece_id);
    if (it == piece_by_id.end())
        return;
    auto &mover = it->second;
    if (cmd.type == "move" && cmd.params.size() >= 2) {
        auto piece_current_cell = mover->current_cell();
        auto command_src_cell = std::any_cast<std::pair<int, int>>(cmd.params[0]);
        if (piece_current_cell != command_src_cell) {
            // Update the command to use the actual piece location
            // (not implemented: would require mutability)
        }
    }
    bool flag = mover->on_command(cmd, pos);
    // Update logs, score, and publish move
    if (flag && cmd.type == "move") {
        std::string cmd_str = command_to_string(cmd);
        if (cmd.piece_id[1] == 'W') {
            game_log_white.add("Move: " + cmd.piece_id);
            score_white.add(1);
            publisher.publish("moves", "white", cmd_str);
        } else if (cmd.piece_id[1] == 'B') {
            game_log_black.add("Move: " + cmd.piece_id);
            score_black.add(1);
            publisher.publish("moves", "black", cmd_str);
        }
    }
}
