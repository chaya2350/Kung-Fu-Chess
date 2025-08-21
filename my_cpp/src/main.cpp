#include "GameFactory.hpp"
#include "GraphicsFactory.hpp"
#include <opencv2/opencv.hpp>
#include <iostream>
#include <SDL.h>

int main(int argc, char* argv[]) {
    std::cout << "Starting chess game..." << std::endl;
    auto imgFactory = ImgFactory();
    auto game = create_game("../../pieces", imgFactory);
    std::cout << "Game created successfully" << std::endl;

    // Load and show start image
    cv::Mat img = cv::imread("../../pic/start.png");
    if (!img.empty()) {
        int game_width = 768 + (2 * 300);
        int game_height = 768;
        cv::Mat img_resized;
        cv::resize(img, img_resized, cv::Size(game_width, game_height));
        cv::imshow("Chess Game", img_resized);
        std::cout << "Start image shown" << std::endl;
    }
    cv::waitKey(3000);
    
    std::cout << "Starting game..." << std::endl;
    game->run(-1, true);  // ריצה אינסופית עם גרפיקה
    std::cout << "Game finished" << std::endl;
    return 0;
}
