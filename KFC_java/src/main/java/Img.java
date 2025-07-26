
// The original Img class is now split into an interface (this file) and concrete
// implementations (BuffImg, MockImg). All graphics-related details live inside
// those implementations so that the rest of the codebase depends only on this
// narrow API.

import java.awt.*;

public interface Img {

    /* -------------- loading -------------- */
    Img read(String path);
    Img read(String path, Dimension targetSize, boolean keepAspect, Object interpolation);

    /* -------------- drawing -------------- */
    void drawOn(Img other, int x, int y);
    void putText(String txt, int x, int y, float fontSize, Color color, int thickness);
    void drawRect(int x1, int y1, int x2, int y2, Color color);

    /* -------------- display -------------- */
    void show();

    /* -------------- raw access (tests only) -------------- */
    java.awt.image.BufferedImage get();
}
