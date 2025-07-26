import java.awt.Dimension;import java.nio.file.Path;import javax.imageio.ImageIO;import java.awt.image.BufferedImage;

public class BoardFactory {
    public static Board loadDefault(Path boardImgPath) {
        try {
            BufferedImage img = ImageIO.read(boardImgPath.toFile());
            int cell = img.getWidth()/8; // assume 8x8
            Img bg = new BuffImg().read(boardImgPath.toString());
            return new Board(cell, cell, 8,8, bg);
        } catch(Exception e){ throw new RuntimeException(e); }
    }
} 