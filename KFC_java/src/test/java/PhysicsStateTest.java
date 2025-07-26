import org.junit.jupiter.api.Test;
import java.awt.Dimension;
import java.nio.file.Path;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

import java.util.ArrayList;

public class PhysicsStateTest {
    /* helper */
    private static Img blankImg(int w, int h) {
        return new MockImg(w, h);
    }
    private static Board board(int cells) {
        int cellPx = 1;
        return new Board(cellPx, cellPx, cells, cells, blankImg(cells, cells));
    }
    private static Graphics graphics() {
        try {
            java.nio.file.Path tmpDir = java.nio.file.Files.createTempDirectory("sprites");
            java.awt.image.BufferedImage dummy = new java.awt.image.BufferedImage(1,1, java.awt.image.BufferedImage.TYPE_INT_ARGB);
            javax.imageio.ImageIO.write(dummy, "png", tmpDir.resolve("a.png").toFile());
            return new Graphics(tmpDir, new Dimension(1,1), false, 1.0);
        } catch(Exception e) { throw new RuntimeException(e); }
    }

    @Test
    void testIdlePhysicsProperties() {
        Board b = board(8);
        Physics.IdlePhysics phys = new Physics.IdlePhysics(b);
        Command cmd = new Command(0, "P", "idle", List.of(new Moves.Pair(2,3)));
        phys.reset(cmd);
        assertEquals(new Moves.Pair(2,3), phys.getCurrCell());
        assertNull(phys.update(100));
        assertTrue(phys.canCapture());
        assertTrue(phys.isMovementBlocker());
    }

    @Test
    void testMovePhysicsFullCycle() {
        Board b = board(8);
        Physics.MovePhysics phys = new Physics.MovePhysics(b, 1.0); // 1 cell/sec
        Command cmd = new Command(0, "P", "move", List.of(new Moves.Pair(0,0), new Moves.Pair(0,2)));
        phys.reset(cmd);
        assertNull(phys.update(1000));
        Command done = phys.update(2100);
        assertNotNull(done);
        assertEquals("done", done.type);
        phys.update(2200);
        assertEquals(new Moves.Pair(0,2), phys.getCurrCell());
    }

    @Test
    void testJumpAndRestPhysics() {
        Board b = board(8);
        Physics.JumpPhysics jump = new Physics.JumpPhysics(b, 0.05);
        Physics.RestPhysics rest = new Physics.RestPhysics(b, 0.05);
        Command start = new Command(0, "J", "jump", List.of(new Moves.Pair(1,1)));
        jump.reset(start);
        rest.reset(start);
        assertNull(jump.update(20));
        assertNull(rest.update(20));
        assertEquals("done", jump.update(100).type);
        assertEquals("done", rest.update(100).type);
        assertFalse(jump.canBeCaptured());
        assertFalse(rest.canCapture());
        assertTrue(rest.isMovementBlocker());
    }

    @Test
    void testStateTransitionsViaInternalDone() {
        Board b = board(8);
        Physics.IdlePhysics idlePhys = new Physics.IdlePhysics(b);
        Physics.JumpPhysics jumpPhys = new Physics.JumpPhysics(b, 0.01);
        Graphics gfxIdle = graphics();
        Graphics gfxJump = graphics();
        State idle = new State(null, gfxIdle, idlePhys);
        State jump = new State(null, gfxJump, jumpPhys);
        idle.name="idle"; jump.name="jump";
        idle.setTransition("jump", jump);
        jump.setTransition("done", idle);
        Piece piece = new Piece("PX", idle);
        piece.onCommand(new Command(0, piece.id, "jump", List.of(new Moves.Pair(0,0))), null);
        assertSame(jump, piece.state);
        piece.update(20);
        assertSame(idle, piece.state);
    }
} 