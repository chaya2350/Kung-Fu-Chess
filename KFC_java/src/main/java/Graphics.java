import java.awt.Dimension;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class Graphics {
    private final List<Img> frames = new ArrayList<>();
    private final boolean loop;
    private final double fps;
    private final double frameDurationMs;
    private long startMs;
    private int curFrame;

    public Graphics(Path spritesFolder, Dimension cellSize, boolean loop, double fps) {
        this.loop = loop;
        this.fps = fps;
        this.frameDurationMs = 1000.0 / fps;
        // load sprites PNGs in alphabetical order – propagate errors instead of silently ignoring
        try (java.util.stream.Stream<java.nio.file.Path> paths = java.nio.file.Files.list(spritesFolder)) {
            paths.filter(p -> p.toString().endsWith(".png"))
                 .sorted()
                 .forEach(p -> frames.add(new BuffImg().read(p.toString(), cellSize, true, null)));
        } catch (java.io.IOException e) {
            throw new RuntimeException("Failed listing sprites folder: " + spritesFolder, e);
        }

        if (frames.isEmpty()) {
            throw new IllegalArgumentException("No PNG sprite frames found in folder: " + spritesFolder);
        }
    }

    public void reset(Command cmd) {
        this.startMs = cmd.timestamp;
        this.curFrame = 0;
    }

    public void update(long nowMs) {
        long elapsed = nowMs - startMs;
        int framesPassed = (int) (elapsed / frameDurationMs);
        if (loop) {
            curFrame = framesPassed % frames.size();
        } else {
            curFrame = Math.min(framesPassed, frames.size() - 1);
        }
    }

    public Img getImg() {
        if (frames.isEmpty()) throw new IllegalStateException("No frames loaded for animation.");
        return frames.get(curFrame);
    }

    // Expose frames per second for tests
    public double getFps() { return fps; }

    // For tests – allow direct access to frames
    public List<Img> getFrames() { return frames; }
    public int getCurFrame() { return curFrame; }
} 