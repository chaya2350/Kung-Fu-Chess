import java.nio.file.*;
import java.awt.Dimension;
import java.util.*;

public class GameFactory {
    public static Game createGame(String piecesRootStr) {
        return createGame(Path.of(piecesRootStr));
    }

    public static Game createGame(Path piecesRoot) {
        // Build an 8x8 board with blank background
        int cellPx = 32;
        Img bg = new BuffImg();
        try {
            java.awt.image.BufferedImage blank = new java.awt.image.BufferedImage(cellPx*8, cellPx*8, java.awt.image.BufferedImage.TYPE_INT_ARGB);
            java.lang.reflect.Field f = BuffImg.class.getDeclaredField("img");
            f.setAccessible(true);
            f.set(bg, blank);
        } catch (Exception e) { throw new RuntimeException(e); }
        Board board = new Board(cellPx, cellPx, 8, 8, bg);

        PieceFactory pFactory = new PieceFactory(board);
        try {
            pFactory.generateLibrary(piecesRoot);
        } catch (Exception e) { throw new RuntimeException("Failed to build piece library", e); }

        // parse board.csv
        Path csvPath = piecesRoot.resolve("board.csv");
        List<Piece> pieces = new ArrayList<>();
        try {
            List<String> lines = Files.readAllLines(csvPath);
            for (int row=0; row<lines.size(); row++) {
                String[] tokens = lines.get(row).strip().split(",");
                for (int col=0; col<tokens.length; col++) {
                    String code = tokens[col].trim();
                    if (code.isEmpty()) continue;
                    Piece piece = pFactory.createPiece(code, new Moves.Pair(row, col));
                    pieces.add(piece);
                }
            }
        } catch (Exception e) { throw new RuntimeException("Failed to parse board.csv", e); }

        return new Game(pieces, board);
    }
} 