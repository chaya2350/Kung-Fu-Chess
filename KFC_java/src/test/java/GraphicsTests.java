import org.junit.jupiter.api.Test;
import java.awt.Dimension;
import java.nio.file.Path;
import static org.junit.jupiter.api.Assertions.*;

public class GraphicsTests {
    private static Graphics makeGraphics(boolean loop, double fps, int numDummyFrames) {
        try {
            java.nio.file.Path tmpDir = java.nio.file.Files.createTempDirectory("sprites");
            // write at least one dummy PNG so constructor succeeds
            java.awt.image.BufferedImage dummy = new java.awt.image.BufferedImage(1,1, java.awt.image.BufferedImage.TYPE_INT_ARGB);
            java.io.File file = tmpDir.resolve("a.png").toFile();
            javax.imageio.ImageIO.write(dummy, "png", file);

            Graphics gfx = new Graphics(tmpDir, new Dimension(32,32), loop, fps);
            // replace frames with dummy placeholders for deterministic tests
            gfx.getFrames().clear();
            for (int i=0;i<numDummyFrames;i++) {
                gfx.getFrames().add(new MockImg());
            }
            return gfx;
        } catch (Exception e) { throw new RuntimeException(e); }
    }

    @Test
    void testAnimationTimingLooping() {
        double fps = 10.0;
        int numFrames = 5;
        Graphics gfx = makeGraphics(true, fps, numFrames);
        gfx.reset(new Command(0, "PX", "idle", java.util.List.of()));
        double frameMs = 1000.0 / fps;
        for (int i=0;i<numFrames;i++) {
            gfx.update((long)(i*frameMs + frameMs/2));
            assertEquals(i, gfx.getCurFrame());
        }
        // after full cycle should wrap to 0
        gfx.update((long)(numFrames*frameMs + frameMs/2));
        assertEquals(0, gfx.getCurFrame());
    }

    @Test
    void testAnimationTimingNonLooping() {
        Graphics gfx = makeGraphics(false, 10.0, 3);
        gfx.reset(new Command(0, "PX", "idle", java.util.List.of()));
        gfx.update(1000); // far beyond animation duration
        assertEquals(2, gfx.getCurFrame()); // stick to last frame
    }

    @Test
    void testEmptyFramesRaises() {
        Graphics gfx = makeGraphics(true, 10.0, 0);
        gfx.reset(new Command(0, "PX", "idle", java.util.List.of()));
        assertThrows(IllegalStateException.class, gfx::getImg);
    }
} 