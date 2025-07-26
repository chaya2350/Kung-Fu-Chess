import org.junit.jupiter.api.Test;
import java.awt.Dimension;
import java.nio.file.Path;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

public class PieceStateGameTest {
    /* helpers */
    private static Img blankImg(int w, int h) {
        return new MockImg(w, h);
    }
    private static Board board(int cells) {
        int cellPx = 32;
        return new Board(cellPx, cellPx, cells, cells, blankImg(cells*cellPx, cells*cellPx));
    }
    private static Graphics graphics() {
        try {
            java.nio.file.Path tmpDir = java.nio.file.Files.createTempDirectory("sprites");
            java.awt.image.BufferedImage dummy = new java.awt.image.BufferedImage(1,1, java.awt.image.BufferedImage.TYPE_INT_ARGB);
            javax.imageio.ImageIO.write(dummy, "png", tmpDir.resolve("a.png").toFile());
            return new Graphics(tmpDir, new Dimension(32,32), false, 1.0);
        } catch(Exception e) { throw new RuntimeException(e); }
    }
    private static Piece makePiece(String id, Moves.Pair cell, Board board) {
        Physics.IdlePhysics idlePhys = new Physics.IdlePhysics(board);
        Physics.MovePhysics movePhys = new Physics.MovePhysics(board, 1.0);
        Physics.JumpPhysics jumpPhys = new Physics.JumpPhysics(board, 0.1);
        Graphics gfx = graphics();
        State idle = new State(null, gfx, idlePhys);
        State move = new State(null, gfx, movePhys);
        State jump = new State(null, gfx, jumpPhys);
        idle.name="idle"; move.name="move"; jump.name="jump";
        idle.setTransition("move", move);
        idle.setTransition("jump", jump);
        move.setTransition("done", idle);
        jump.setTransition("done", idle);
        Piece piece = new Piece(id, idle);
        piece.reset(0);
        idle.reset(new Command(0, id, "idle", List.of(cell)));
        return piece;
    }

    @Test
    void testPieceStateTransitions() {
        Board b = board(8);
        Piece piece = makePiece("PX", new Moves.Pair(4,4), b);
        assertEquals("idle", piece.state.name);
        assertEquals(new Moves.Pair(4,4), piece.currentCell());
        piece.onCommand(new Command(100, piece.id, "move", List.of(new Moves.Pair(4,4), new Moves.Pair(4,5))), null);
        assertEquals("move", piece.state.name);
        piece.update(1200);
        assertEquals("idle", piece.state.name);
        piece.onCommand(new Command(1300, piece.id, "jump", List.of(new Moves.Pair(4,4))), null);
        assertEquals("jump", piece.state.name);
        piece.update(1500);
        assertEquals("idle", piece.state.name);
    }

    @Test
    void testPieceMovementBlocker() {
        Board b = board(8);
        Piece piece = makePiece("PX", new Moves.Pair(4,4), b);
        assertTrue(piece.isMovementBlocker());
        piece.onCommand(new Command(0, piece.id, "move", List.of(new Moves.Pair(4,4), new Moves.Pair(4,5))), null);
        assertFalse(piece.isMovementBlocker());
    }

    @Test
    void testStateInvalidTransitions() {
        Board b = board(8);
        Piece piece = makePiece("PX", new Moves.Pair(4,4), b);
        piece.onCommand(new Command(0, piece.id, "invalid", List.of()), null);
        assertEquals("idle", piece.state.name);
        piece.onCommand(new Command(0, piece.id, "move", List.of()), null);
        assertEquals("idle", piece.state.name);
    }

    @Test
    void testGameInitializationValidation() {
        Board b = board(8);
        Piece whiteKing = makePiece("KW_1", new Moves.Pair(7,4), b);
        Piece blackKing = makePiece("KB_1", new Moves.Pair(0,4), b);
        Game game = new Game(List.of(whiteKing, blackKing), b);
        assertNotNull(game);
        assertThrows(Game.InvalidBoard.class, () -> new Game(List.of(whiteKing), b));
        Piece piece1 = makePiece("PW_1", new Moves.Pair(4,4), b);
        Piece piece2 = makePiece("PW_2", new Moves.Pair(4,4), b);
        assertThrows(Game.InvalidBoard.class, () -> new Game(List.of(whiteKing, blackKing, piece1, piece2), b));
    }

    @Test
    void testGameCollisionResolution() {
        Board b = board(8);
        Piece whiteKing = makePiece("KW_1", new Moves.Pair(7,4), b);
        Piece blackKing = makePiece("KB_1", new Moves.Pair(0,4), b);
        Piece pawn1 = makePiece("PW_1", new Moves.Pair(4,4), b);
        Piece pawn2 = makePiece("PB_1", new Moves.Pair(4,4), b);
        Game game = new Game(new ArrayList<>(List.of(whiteKing, blackKing, pawn1, pawn2)), b);
        pawn1.state.physics.startMs = 100; // earlier
        pawn2.state.physics.startMs = 200; // later
        game._resolve_collisions();
        assertTrue(game.pieces.contains(pawn2));
        assertFalse(game.pieces.contains(pawn1));
    }

    @Test
    void testGameKeyboardInput() {
        Board b = board(8);
        Piece whiteKing = makePiece("KW_1", new Moves.Pair(7,4), b);
        Piece blackKing = makePiece("KB_1", new Moves.Pair(0,4), b);
        Game game = new Game(List.of(whiteKing, blackKing), b);
        Command cmd = new Command(game.game_time_ms(), whiteKing.id, "move", List.of(new Moves.Pair(7,4), new Moves.Pair(6,4)));
        game.userInputQueue.add(cmd);
        game._update_cell2piece_map();
        while (!game.userInputQueue.isEmpty()) {
            game._process_input(game.userInputQueue.poll());
        }
        assertEquals("move", whiteKing.state.name);
    }
} 