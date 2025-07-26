public class KeyboardProducer extends Thread {
    private final Game game;
    private final java.util.concurrent.BlockingQueue<Command> queue;
    private final KeyboardProcessor processor;
    private final int player;
    private volatile boolean running = true;

    public KeyboardProducer(Game game,
                            java.util.concurrent.BlockingQueue<Command> queue,
                            KeyboardProcessor processor,
                            int player) {
        this.game = game;
        this.queue = queue;
        this.processor = processor;
        this.player = player;
        setDaemon(true); // ensure JVM can exit without waiting
    }

    @Override
    public void run() {
        // Currently, we do not capture real keyboard input. This stub keeps the thread alive
        // so that tests can validate start/stop behaviour without blocking.
        try {
            while (running) {
                Thread.sleep(100);
            }
        } catch (InterruptedException ignored) {
            // Thread interrupted when stopping – exit gracefully
        }
    }

    /** Request the background thread to stop and interrupt any sleep. */
    public void stopProducer() {
        running = false;
        this.interrupt();
    }

    /** Access to the associated KeyboardProcessor for tests or external use. */
    public KeyboardProcessor getProcessor() { return processor; }

    /** Return the player number (1 or 2). */
    public int getPlayer() { return player; }
} 