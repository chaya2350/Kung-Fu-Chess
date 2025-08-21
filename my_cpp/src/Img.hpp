#pragma once
#include <opencv2/opencv.hpp>
#include <string>
#include <iostream>

class Img {
public:
    cv::Mat img;

    Img() : img() {}

    Img& read(const std::string& path,
              std::pair<int, int> size = {-1, -1},
              bool keep_aspect = false,
              int interpolation = cv::INTER_AREA);

    Img copy() const {
        Img new_img;
        new_img.img = img.clone();
        return new_img;
    }

    void draw_on(Img& other_img, int x, int y) {
        if (img.empty() || other_img.img.empty()) {
            throw std::runtime_error("Both images must be loaded before drawing.");
        }
        int src_channels = img.channels();
        int dst_channels = other_img.img.channels();
        cv::Mat src = img;
        if (src_channels != dst_channels) {
            if (src_channels == 3 && dst_channels == 4) {
                cv::cvtColor(img, src, cv::COLOR_BGR2BGRA);
            } else if (src_channels == 4 && dst_channels == 3) {
                cv::cvtColor(img, src, cv::COLOR_BGRA2BGR);
            }
        }
        int h = src.rows, w = src.cols;
        int H = other_img.img.rows, W = other_img.img.cols;
        if (h == 0 || w == 0 || y < 0 || x < 0 || y + h > H || x + w > W) {
            return;
        }
        cv::Mat roi = other_img.img(cv::Rect(x, y, w, h));
        if (src.channels() == 4) {
            std::vector<cv::Mat> bgra;
            cv::split(src, bgra);
            cv::Mat mask;
            bgra[3].convertTo(mask, CV_32F, 1.0 / 255.0);
            for (int c = 0; c < 3; ++c) {
                cv::Mat roi_channel, src_channel;
                std::vector<cv::Mat> roi_channels;
                cv::split(roi, roi_channels);
                roi_channels[c].convertTo(roi_channel, CV_32F);
                bgra[c].convertTo(src_channel, CV_32F);
                roi_channel = (1.0 - mask).mul(roi_channel) + mask.mul(src_channel);
                roi_channel.convertTo(roi_channels[c], roi.type());
                cv::merge(roi_channels, roi);
            }
        } else {
            src.copyTo(roi);
        }
    }

    void put_text(const std::string& txt, int x, int y, double font_size, cv::Scalar color = cv::Scalar(255,255,255,255), int thickness = 1) {
        if (img.empty()) {
            throw std::runtime_error("Image not loaded.");
        }
        cv::putText(img, txt, cv::Point(x, y), cv::FONT_HERSHEY_SIMPLEX, font_size, color, thickness, cv::LINE_AA);
    }

    void show() {
        if (img.empty()) {
            throw std::runtime_error("Image not loaded.");
        }
        cv::imshow("Chess Game", img);
        cv::waitKey(1);
    }

    void draw_rect(int x1, int y1, int x2, int y2, cv::Scalar color) {
        cv::rectangle(img, cv::Point(x1, y1), cv::Point(x2, y2), color, 2);
    }
};
