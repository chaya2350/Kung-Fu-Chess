#pragma once

#include <memory>
#include <string>
#include <utility>
#include "Img.hpp"

class ImgFactory {
public:
    virtual ~ImgFactory() = default;

    virtual std::shared_ptr<Img> load(const std::string& path,
                                      const std::pair<int,int>& size = {0,0}) = 0;

    virtual std::shared_ptr<Img> create_blank(int width, int height) = 0;
}; 