
#pragma once
#include <functional>
#include <filesystem>
#include <map>
#include <memory>
#include <string>
#include <utility>
#include <nlohmann/json.hpp>

#include "Graphics.hpp"
#include "Img.hpp"
#include "MockImg.hpp"

class ImgFactory {
public:
    Img operator()(const std::filesystem::path& path, std::pair<int, int> size, bool keep_aspect = false) const {
        return Img().read(path.string(), size, keep_aspect);
    }
};

class MockImgFactory : public ImgFactory {
public:
    MockImg operator()(const std::filesystem::path& path, std::pair<int, int> size, bool keep_aspect = false) const {
        return MockImg().read(path.string(), size, keep_aspect);
    }
};

class GraphicsFactory {

public:
    std::function<Img(const std::filesystem::path&, std::pair<int, int>, bool)> _img_factory;

    GraphicsFactory()
        : _img_factory([](const std::filesystem::path&, std::pair<int, int>, bool) { return Img(); }) {}

    GraphicsFactory(std::function<Img(const std::filesystem::path&, std::pair<int, int>, bool)> img_factory)
        : _img_factory(img_factory) {}

    std::unique_ptr<Graphics> load(const std::filesystem::path& sprites_dir,
                                   const nlohmann::json& cfg,
                                   std::pair<int, int> cell_size) {
        bool loop = true;
        double fps = 6.0;
        if (cfg.contains("is_loop")) loop = cfg["is_loop"].get<bool>();
        if (cfg.contains("frames_per_sec")) fps = cfg["frames_per_sec"].get<double>();
        return std::make_unique<Graphics>(sprites_dir, cell_size, _img_factory, loop, static_cast<float>(fps));
    }
};
