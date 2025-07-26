import org.junit.jupiter.api.Test;
import java.awt.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.Set;
import static org.junit.jupiter.api.Assertions.*;

public class BoardMovesImgTest {

    /* ---------------- helpers --------------- */
    private static Img blankImg(int w, int h) {
        return new MockImg(w, h);
    }

    /* ---------------- BOARD ---------------- */
    @Test
    void testBoardCellConversions() {
        Board board = new Board(2, 2, 4, 4, blankImg(8, 8));
        int[] cell = {2, 1};
        double[] metres = board.cellToM(cell[0], cell[1]);
        int[] pix = board.mToPix(metres[0], metres[1]);
        int[] backCell = board.mToCell(metres[0], metres[1]);
        assertArrayEquals(cell, backCell);
        assertArrayEquals(new int[]{1 * board.getCellWPix(), 2 * board.getCellHPix()}, pix);
        board.show(); // should not crash headless
    }

    /* ---------------- IMG ---------------- */
    @Test
    void testImgDrawAndRectangle() {
        Img dst = blankImg(4, 4);
        Img src = blankImg(2, 2);
        src.drawOn(dst, 1, 1);
        dst.drawRect(0, 0, 3, 3, new Color(255, 0, 0));
    }

    /* ---------------- MOVES ---------------- */
    @Test
    void testMovesParsingAndValidation() throws Exception {
        String movesTxt = "1,0:capture\n-1,0:non_capture\n0,1:\n";
        Path filePath = Files.createTempFile("moves", ".txt");
        Files.writeString(filePath, movesTxt);
        Moves mv = new Moves(filePath, 8, 8);

        // occupied set representation
        Set<Moves.Pair> occupied = new HashSet<>();
        // capture move allowed only if dst_has_piece
        assertTrue(mv.isDstCellValid(1, 0, true));
        assertFalse(mv.isDstCellValid(1, 0, false));
        // non-capture move
        assertTrue(mv.isDstCellValid(-1, 0, false));
        assertFalse(mv.isDstCellValid(-1, 0, true));
        // can both
        assertTrue(mv.isDstCellValid(0, 1, false));
        assertTrue(mv.isDstCellValid(0, 1, true));
    }
} 