#pragma once

#include "Img.hpp"
#include <memory>
#include <string>
#include <utility>

// Concrete Img backed by OpenCV cv::Mat.  All OpenCV headers are
// confined to the .cpp implementation to avoid leaking cv symbols to
// the rest of the codebase.
class OpenCvImg : public Img {
public:
    OpenCvImg();
    ~OpenCvImg() override;

    void read(const std::string& path,
              const std::pair<int,int>& size = {0,0}) override;
    void draw_on(Img& dst, int x, int y) override;
    void put_text(const std::string& txt, int x, int y, double font_size) override;
    void show() const override;

    // Internal helper for factories/tests – create a blank image of given size
    void create_blank(int width, int height);

private:
    struct Impl;
    std::unique_ptr<Impl> impl;
}; 