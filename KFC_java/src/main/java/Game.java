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

    public void run() {
        // simple single-frame demo: update map and show board once
        _update_cell2piece_map();
        board.show();
    }
} 