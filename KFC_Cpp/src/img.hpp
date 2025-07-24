#pragma once

#if __has_include(<opencv2/opencv.hpp>)
#  include <opencv2/opencv.hpp>
#  define KFC_HAVE_OPENCV 1
#else
#  define KFC_HAVE_OPENCV 0
#  include <string>
#  include <vector>

namespace cv {

struct Size {
    int width;
    int height;
    Size(int w, int h) : width(w), height(h) {}
};

struct Scalar {
    double v0, v1, v2, v3;
    Scalar(double a, double b, double c, double d) : v0(a), v1(b), v2(c), v3(d) {}
};

struct Point { int x; int y; Point(int x_, int y_) : x(x_), y(y_) {} };

struct Mat {
    int rows{0};
    int cols{0};
    std::vector<unsigned char> data;  // placeholder

    bool empty() const { return rows == 0 || cols == 0; }
    int channels() const { return 4; }
};

inline Mat imread(const std::string&, int) { return {}; }
inline void resize(Mat&, Mat&, Size, double=0, double=0, int=0) {}
inline void cvtColor(const Mat&, Mat&, int) {}
inline void split(const Mat&, std::vector<Mat>&) {}
inline void putText(Mat&, const std::string&, cv::Point, int, double, cv::Scalar, int, int) {}
inline void imshow(const std::string&, const Mat&) {}
inline int waitKey(int=0) { return 0; }
inline void destroyAllWindows() {}

// Colour conversion flags and interpolation constants – dummy values
inline constexpr int COLOR_BGR2BGRA = 0;
inline constexpr int COLOR_BGRA2BGR = 1;
inline constexpr int INTER_AREA = 2;
inline constexpr int INTER_LINEAR = 3;
inline constexpr int IMREAD_UNCHANGED = 4;

} // namespace cv
#endif

#include <string>
#include <filesystem>

class Img {
public:
    Img();

    // Utility for tests/internal: directly assign an existing cv::Mat
    void set_mat(const cv::Mat& m) { img = m; }
    
    /**
     * Load image from path and optionally resize.
     * 
     * @param path Image file to load
     * @param size Target size in pixels (width, height). If empty, keep original
     * @param keep_aspect If true, shrink so the longer side fits size while preserving aspect ratio
     * @param interpolation OpenCV interpolation flag (e.g., cv::INTER_AREA for shrink, cv::INTER_LINEAR for enlarge)
     * @return Reference to this object for method chaining
     */
    Img& read(const std::string& path,
              const std::pair<int, int>& size = {},
              bool keep_aspect = false,
              int interpolation = cv::INTER_AREA);
    
    /**
     * Draw this image onto another image at position (x, y)
     * 
     * @param other_img The target image to draw on
     * @param x X coordinate for top-left corner
     * @param y Y coordinate for top-left corner
     */
    void draw_on(Img& other_img, int x, int y);
    
    /**
     * Put text on the image
     * 
     * @param txt Text to draw
     * @param x X coordinate for text position
     * @param y Y coordinate for text position (baseline)
     * @param font_size Font scale factor
     * @param color Text color (BGR or BGRA)
     * @param thickness Text thickness
     */
    void put_text(const std::string& txt, int x, int y, double font_size,
                  const cv::Scalar& color = cv::Scalar(255, 255, 255, 255),
                  int thickness = 1);
    
    /**
     * Display the image in a window
     */
    void show() const;
    
    /**
     * Get the underlying OpenCV Mat
     */
    const cv::Mat& get_mat() const { return img; }
    
    /**
     * Check if image is loaded
     */
    bool is_loaded() const { return !img.empty(); }

private:
    cv::Mat img;
}; 