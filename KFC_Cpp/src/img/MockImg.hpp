#pragma once

#include "Img.hpp"
#include <memory>
#include "ImgFactory.hpp"

class MockImg : public Img {
private:
    std::pair<int,int> _size;
public:
    MockImg(std::pair<int,int> size) : _size(size) {}
    std::pair<int,int> size() const override { return _size; }
    void read(const std::string&, const std::pair<int,int>&) override {}
    void draw_on(Img&, int, int) override {}
    void put_text(const std::string&, int, int, double) override {}
    void show() const override {}
    ImgPtr clone() const override { return std::make_shared<MockImg>(); }

};

class MockImgFactory : public ImgFactory {
public:
    ImgPtr load(const std::string& /*path*/,
                const std::pair<int,int>& /*size*/ = {0,0}) override {
        return std::make_shared<MockImg>();
    }

    ImgPtr create_blank(int /*width*/, int /*height*/) const override {
        return std::make_shared<MockImg>();
    }
}; 