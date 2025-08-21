#pragma once
#include "Img.hpp"
#include "Command.hpp"
#include <vector>
#include <string>
#include <memory>
#include <filesystem>
#include <algorithm>
#include <stdexcept>
#include <iostream>

class Graphics {
public:
    std::vector<Img> frames;
    bool loop;
    float fps;
    int start_ms;
    int cur_frame;
    float frame_duration_ms;

    // img_loader: function pointer or functor
    using ImgLoader = std::function<Img(const std::filesystem::path&, std::pair<int, int>, bool)>;
    ImgLoader _img_loader;

    Graphics(const std::filesystem::path& sprites_folder,
             std::pair<int, int> cell_size,
             ImgLoader img_loader,
             bool loop_ = true,
             float fps_ = 6.0f)
        : _img_loader(img_loader), loop(loop_), fps(fps_), start_ms(0), cur_frame(0), frame_duration_ms(1000.0f / fps_) {
        frames = _load_sprites(sprites_folder, cell_size);
    }

    Graphics copy() const {
        return *this; // shallow copy is enough
    }

    std::vector<Img> _load_sprites(const std::filesystem::path& folder, std::pair<int, int> cell_size) {
        std::vector<Img> frames;
        std::vector<std::filesystem::path> files;
        for (auto& p : std::filesystem::directory_iterator(folder)) {
            if (p.path().extension() == ".png") files.push_back(p.path());
        }
        std::sort(files.begin(), files.end());
        for (const auto& p : files) {
            frames.push_back(_img_loader(p, cell_size, false));
        }
        if (frames.empty()) {
            throw std::runtime_error("No frames found in " + folder.string());
        }
        return frames;
    }

    void reset(const Command& cmd) {
        start_ms = cmd.timestamp;
        cur_frame = 0;
    }

    void update(int now_ms) {
        int elapsed = now_ms - start_ms;
        int frames_passed = static_cast<int>(elapsed / frame_duration_ms);
        if (loop) {
            cur_frame = frames_passed % frames.size();
        } else {
            cur_frame = std::min(frames_passed, static_cast<int>(frames.size()) - 1);
        }
    }

    Img get_img() const {
        if (frames.empty()) throw std::runtime_error("No frames loaded for animation.");
        if (cur_frame >= static_cast<int>(frames.size())) throw std::runtime_error("Frame index out of range");
        return frames[cur_frame];
    }
};