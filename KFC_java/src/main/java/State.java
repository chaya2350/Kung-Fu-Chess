import java.util.*;

public class State {
    public Moves moves;            // optional may be null
    public Graphics graphics;
    public Physics physics;
    private final Map<String, State> transitions = new HashMap<>();
    public String name;

    public State(Moves moves, Graphics graphics, Physics physics) {
        this.moves = moves;
        this.graphics = graphics;
        this.physics = physics;
    }

    @Override public String toString() { return "State(" + name + ")"; }

    public void setTransition(String event, State target) { transitions.put(event.toLowerCase(), target); }

    public Map<String, State> getTransitions() { return transitions; }

    public void reset(Command cmd) {
        graphics.reset(cmd);
        physics.reset(cmd);
    }

    public State onCommand(Command cmd, java.util.Map<Moves.Pair, java.util.List<Piece>> cell2piece) {
        String key = cmd.type.toLowerCase();

        State next = transitions.get(key);
        if (next == null) return this;   // no transition defined

        // ─── additional legality checks for MOVE commands ────────────────
        if ("move".equals(key) && moves != null && cmd.params != null && cmd.params.size() >= 2 && cell2piece != null) {
            Moves.Pair src = (Moves.Pair) cmd.params.get(0);
            Moves.Pair dst = (Moves.Pair) cmd.params.get(1);

            // ensure the source matches the physics-reported current cell
            if (!src.equals(physics.getCurrCell())) {
                return this; // reject – stale source
            }

            java.util.Set<Moves.Pair> occupied = cell2piece.keySet();
            int[] srcArr = new int[]{src.r, src.c};
            int[] dstArr = new int[]{dst.r, dst.c};
            if (!moves.isValid(srcArr, dstArr, occupied)) {
                return this; // illegal destination / path blocked
            }
        }

        // -----------------------------------------------------------------
        next.reset(cmd);
        return next;
    }

    public State update(long nowMs) {
        Command internal = physics.update(nowMs);
        if (internal != null) {
            return onCommand(internal, null);
        }
        return this;
    }

    public boolean canBeCaptured() { return physics.canBeCaptured(); }
    public boolean canCapture() { return physics.canCapture(); }
} 