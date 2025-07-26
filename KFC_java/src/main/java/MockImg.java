import java.awt.*;
import java.awt.image.BufferedImage;

/**
 * Lightweight stub image implementation for unit tests – avoids any Swing or disk I/O.
 */
public class MockImg implements Img {

    private BufferedImage img;

    public MockImg() {}
    public MockImg(int w, int h) { this.img = new BufferedImage(w, h, BufferedImage.TYPE_INT_ARGB); }

    /* ---------------- loading ---------------- */
    @Override
    public Img read(String path) { return this; } // no-op

    @Override
    public Img read(String path, Dimension targetSize, boolean keepAspect, Object interpolation) { return this; }

    /* ---------------- drawing ---------------- */
    @Override
    public void drawOn(Img other, int x, int y) {
        // For test purposes, we don't simulate pixel copying – it's enough that the call succeeds.
    }

    @Override
    public void putText(String txt, int x, int y, float fontSize, Color color, int thickness) { /* noop */ }

    @Override
    public void drawRect(int x1, int y1, int x2, int y2, Color color) {
        if (img == null) return;
        Graphics2D g = img.createGraphics();
        g.setColor(color);
        g.drawRect(x1, y1, x2 - x1, y2 - y1);
        g.dispose();
    }

    /* ---------------- display ---------------- */
    @Override
    public void show() { /* nothing – headless */ }

    /* ---------------- access ---------------- */
    @Override
    public BufferedImage get() { return img; }

    /* Convenience factory for blank mock */
    public static MockImg blank(int w, int h) { return new MockImg(w, h); }
} 