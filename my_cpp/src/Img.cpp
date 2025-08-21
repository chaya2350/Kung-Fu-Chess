
#include "Img.hpp"
#include <opencv2/opencv.hpp>
#include <string>
#include <iostream>
#include <algorithm>
#include <fstream>
#include <filesystem>

Img& Img::read(const std::string& path,
              std::pair<int, int> size,
              bool keep_aspect,
              int interpolation) {
    img = cv::imread(path, cv::IMREAD_UNCHANGED);
    if (img.empty()) {
        throw std::runtime_error("Cannot load image: " + path);
    }
    if (size.first > 0 && size.second > 0) {
        int target_w = size.first;
        int target_h = size.second;
        int h = img.rows;
        int w = img.cols;
        int new_w, new_h;
        if (keep_aspect) {
            double scale = std::min(target_w / (double)w, target_h / (double)h);
            new_w = std::max(1, static_cast<int>(w * scale));
            new_h = std::max(1, static_cast<int>(h * scale));
        } else {
            new_w = target_w;
            new_h = target_h;
        }
        cv::resize(img, img, cv::Size(new_w, new_h), 0, 0, interpolation);
        if (img.rows == 0 || img.cols == 0) {
            throw std::runtime_error("Invalid resized image: " + path);
        }
    }
    return *this;
}
