#pragma once

#include "Img.hpp"
#include <memory>

class MockImg : public Img {
public:
    void read(const std::string&, const std::pair<int,int>&) override {}
    void draw_on(Img&, int, int) override {}
    void put_text(const std::string&, int, int, double) override {}
    void show() const override {}
}; 