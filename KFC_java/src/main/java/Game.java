import java.util.*;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;

public class Game {
    public static class InvalidBoard extends RuntimeException {}

    public final List<Piece> pieces;
    public final Board board;
    private final long startNs;
    private long timeFactor = 1; // multiplier for faster tests
    public final BlockingQueue<Command> userInputQueue = new LinkedBlockingQueue<>();
    public final Map<Moves.Pair, List<Piece>> pos = new HashMap<>();
    public final Map<String, Piece> pieceById = new HashMap<>();

    // --- keyboard helpers -----------------------------------------------------
    private KeyboardProcessor kp1, kp2;
    private KeyboardProducer kbProd1, kbProd2;

    public Game(List<Piece> pieces, Board board) {
        if (!validate(pieces)) throw new InvalidBoard();
        this.pieces = new ArrayList<>(pieces);
        this.board = board;
        this.startNs = System.nanoTime();
        for (Piece p : pieces) pieceById.put(p.id, p);
    }

    private boolean validate(List<Piece> pieces) {
        Map<Moves.Pair, Character> occupantSide = new HashMap<>();
        boolean wKing=false, bKing=false;
        for (Piece p: pieces) {
            Moves.Pair cell = p.currentCell();
            char side = p.id.charAt(1); // 'W' or 'B'
            Character prev = occupantSide.get(cell);
            if (prev != null && prev == side) {
                return false; // same-side duplicate
            }
            occupantSide.put(cell, side);
            if (p.id.startsWith("KW")) wKing=true;
            if (p.id.startsWith("KB")) bKing=true;
        }
        return wKing && bKing;
    }

    public long game_time_ms() { return ((System.nanoTime() - startNs)/1_000_000) * timeFactor; }

    public void setTimeFactor(long factor) { this.timeFactor = factor; }

    /* ---------------- win detection --------------- */
    public boolean _is_win() {
        long kings = pieces.stream().filter(p -> p.id.startsWith("KW") || p.id.startsWith("KB")).count();
        return kings < 2;
    }

    /* ---------------- simplified game loop (no graphics) ------------ */
    public void _run_game_loop(int numIterations, boolean withGraphics) {
        int counter = 0;
        while (!_is_win()) {
            long now = game_time_ms();
            for (Piece p: new ArrayList<>(pieces)) {
                p.update(now);
            }

            _update_cell2piece_map();

            while (!userInputQueue.isEmpty()) {
                Command cmd = userInputQueue.poll();
                _process_input(cmd);
            }

            _resolve_collisions();

            if (numIterations > 0 && ++counter >= numIterations) {
                break;
            }
        }
    }

    public void _update_cell2piece_map() {
        pos.clear();
        for (Piece p: pieces) {
            pos.computeIfAbsent(p.currentCell(), k->new ArrayList<>()).add(p);
        }
    }

    public void _process_input(Command cmd) {
        Piece mover = pieceById.get(cmd.pieceId);
        if (mover == null) return;
        mover.onCommand(cmd, pos);
    }

    public void _resolve_collisions() {
        Map<Moves.Pair, List<Piece>> occupied = new HashMap<>();
        for (Piece p: pieces) {
            occupied.computeIfAbsent(p.currentCell(), k->new ArrayList<>()).add(p);
        }
        for (Map.Entry<Moves.Pair, List<Piece>> entry: occupied.entrySet()) {
            List<Piece> plist = entry.getValue();
            if (plist.size()<2) continue;
            Piece winner = plist.stream().max(Comparator.comparingLong(p -> p.state.physics.getStartMs())).orElse(null);
            if (winner==null || !winner.state.canCapture()) continue;
            for (Piece p: new ArrayList<>(plist)) {
                if (p==winner) continue;
                if (p.state.canBeCaptured()) pieces.remove(p);
            }
        }
    }

    /* ---------------- keyboard helpers ---------------- */
    public void startUserInputThread() {
        // player 1 key-map
        Map<String,String> p1Map = Map.of(
                "up", "up", "down", "down", "left", "left", "right", "right",
                "enter", "select", "+", "jump"
        );
        // player 2 key-map
        Map<String,String> p2Map = Map.of(
                "w", "up", "s", "down", "a", "left", "d", "right",
                "f", "select", "g", "jump"
        );

        // create two processors
        kp1 = new KeyboardProcessor(board.getHCells(), board.getWCells(), p1Map);
        kp2 = new KeyboardProcessor(board.getHCells(), board.getWCells(), p2Map);

        // pass the player number as the 4th argument
        kbProd1 = new KeyboardProducer(this, userInputQueue, kp1, 1);
        kbProd2 = new KeyboardProducer(this, userInputQueue, kp2, 2);

        kbProd1.start();
        kbProd2.start();
    }

    private void _announce_win() {
        boolean blackWins = pieces.stream().anyMatch(p -> p.id.startsWith("KB"));
        String text = blackWins ? "Black wins!" : "White wins!";
        System.out.println(text);
    }

    // Accessors for tests
    public KeyboardProducer getKbProd1() { return kbProd1; }
    public KeyboardProducer getKbProd2() { return kbProd2; }

    public void stopUserInputThreads() {
        if (kbProd1 != null) kbProd1.stopProducer();
        if (kbProd2 != null) kbProd2.stopProducer();
    }

    public void run() {
        // Mirror Python's Game.run implementation
        startUserInputThread();
        long startMs = game_time_ms();
        for (Piece p : pieces) {
            p.reset(startMs);
        }

        // pass 0 iterations to signify unlimited loop, graphics flag true (ignored currently)
        _run_game_loop(0, true);

        _announce_win();
        if (kbProd1 != null) kbProd1.stopProducer();
        if (kbProd2 != null) kbProd2.stopProducer();
    }
} 