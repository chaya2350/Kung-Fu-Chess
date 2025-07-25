#include "OpenCvImg.hpp"

#if __has_include(<opencv2/opencv.hpp>)
#include <opencv2/opencv.hpp>
#endif
#include <stdexcept>
#include <vector>

struct OpenCvImg::Impl {
#if KFC_HAVE_OPENCV
    cv::Mat mat;
#else
    cv::Mat mat; // stub definition from header
#endif
};

OpenCvImg::OpenCvImg() : impl(std::make_unique<Impl>()) {}
OpenCvImg::~OpenCvImg() = default;

void OpenCvImg::read(const std::string& path, const std::pair<int,int>& size) {
#if KFC_HAVE_OPENCV
    impl->mat = cv::imread(path, cv::IMREAD_UNCHANGED);
    if(impl->mat.empty()) throw std::runtime_error("Cannot load image: " + path);
    if(size.first>0 && size.second>0) {
        cv::resize(impl->mat, impl->mat, cv::Size(size.first,size.second));
    }
#else
    (void)path; (void)size;
#endif
}

void OpenCvImg::create_blank(int w,int h) {
#if KFC_HAVE_OPENCV
    impl->mat = cv::Mat(h,w,CV_8UC4, cv::Scalar(0,0,0,0));
#else
    impl->mat.rows = h; impl->mat.cols = w;
#endif
}

void OpenCvImg::draw_on(Img& dst,int x,int y) {
    auto* cvDst = dynamic_cast<OpenCvImg*>(&dst);
    if(!cvDst) return;
#if KFC_HAVE_OPENCV
    if(impl->mat.empty()) return;
    impl->mat.copyTo(cvDst->impl->mat(cv::Rect(x,y,impl->mat.cols,impl->mat.rows)));
#else
    (void)x; (void)y;
#endif
}

void OpenCvImg::put_text(const std::string& txt,int x,int y,double font_size) {
#if KFC_HAVE_OPENCV
    if(impl->mat.empty()) return;
    cv::putText(impl->mat, txt, cv::Point(x,y), cv::FONT_HERSHEY_SIMPLEX, font_size, cv::Scalar(255,255,255,255));
#else
    (void)txt;(void)x;(void)y;(void)font_size;
#endif
}

void OpenCvImg::show() const {
#if KFC_HAVE_OPENCV
    if(impl->mat.empty()) return;
    cv::imshow("Image", impl->mat);
    cv::waitKey(1);
#endif
} 