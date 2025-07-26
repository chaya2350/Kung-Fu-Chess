import org.junit.jupiter.api.Test;
import java.nio.file.Path;
import static org.junit.jupiter.api.Assertions.*;

public class KeyboardProducerTest {

    private static final Path PIECES_DIR = Path.of("..", "KungFu Chess", "pieces");

    @Test
    void testProducerThreadLifecycle() throws InterruptedException {
        Game game = GameFactory.createGame(PIECES_DIR);
        // start threads
        game.startUserInputThread();
        KeyboardProducer kb1 = game.getKbProd1();
        KeyboardProducer kb2 = game.getKbProd2();
        assertNotNull(kb1);
        assertNotNull(kb2);

        // give threads time to start
        Thread.sleep(100);
        assertTrue(kb1.isAlive(), "kbProd1 should be alive after startUserInputThread()");
        assertTrue(kb2.isAlive(), "kbProd2 should be alive after startUserInputThread()");

        // stop threads
        game.stopUserInputThreads();
        kb1.join(1000);
        kb2.join(1000);
        assertFalse(kb1.isAlive(), "kbProd1 should terminate after stop");
        assertFalse(kb2.isAlive(), "kbProd2 should terminate after stop");
    }
} 