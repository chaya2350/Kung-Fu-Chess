#pragma once

#include "Graphics.hpp"
#include <memory>
#include <string>
#include <optional>
#include "img/ImgFactory.hpp"

namespace nlohmann { class json; }

// Simple GraphicsFactory that forwards an image loader placeholder to
// Graphics.  In this head-less C++ port, the img_loader is unused but the
// factory mirrors the Python API expected by the unit tests.
class GraphicsFactory {
public:
    explicit GraphicsFactory(std::shared_ptr<ImgFactory> factory_ptr = nullptr)
        : img_factory(std::move(factory_ptr)) {}

    std::shared_ptr<Graphics> load(const std::string& sprites_dir,
                                   const nlohmann::json& /*cfg*/, // ignored
                                   std::pair<int,int> cell_size) const {
        // For now, create a Graphics object with blank frames produced by img_factory
        auto gfx = std::make_shared<Graphics>(sprites_dir, cell_size, /*loop*/true, /*fps*/6.0);
        if(img_factory) {
            auto blank = img_factory->create_blank(cell_size.first, cell_size.second);
            gfx->set_frames({*blank}); // will adapt when Graphics updated to shared_ptr
        }
        return gfx;
    }
private:
    std::shared_ptr<ImgFactory> img_factory;
}; 