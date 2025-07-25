#pragma once

#include <string>
#include <utility>

class Img {
public:
    virtual ~Img() = default;

    virtual void read(const std::string& path,
                      const std::pair<int,int>& size = {0,0}) = 0;
    virtual void draw_on(Img& dst, int x, int y) = 0;
    virtual void put_text(const std::string& txt, int x, int y, double font_size) = 0;
    virtual void show() const = 0;
}; 