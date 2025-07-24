import java.nio.file.*;import java.util.*;import java.awt.Dimension;import org.json.*;

public class PieceFactory {
    private final Board board; private final GraphicsFactory gfxFactory; private final PhysicsFactory physFactory;
    private final Map<String, State> templates = new HashMap<>();

    public PieceFactory(Board board){this.board=board;this.gfxFactory=new GraphicsFactory();this.physFactory=new PhysicsFactory(board);}    

    public void generateLibrary(Path piecesRoot) throws Exception {
        try (DirectoryStream<Path> stream = Files.newDirectoryStream(piecesRoot)){
            for(Path sub: stream){ if(Files.isDirectory(sub)) templates.put(sub.getFileName().toString(), buildStateMachine(sub)); }
        }
    }

    private State buildStateMachine(Path pieceDir) throws Exception {
        int W=board.getWCells(), H=board.getHCells();
        Dimension cellPx=new Dimension(board.getCellWPix(), board.getCellHPix());
        Map<String, State> states=new HashMap<>();
        Path statesDir=pieceDir.resolve("states");
        if(!Files.exists(statesDir)) throw new IllegalStateException("Missing states dir: "+statesDir);
        try(DirectoryStream<Path> stream = Files.newDirectoryStream(statesDir)){
            for(Path stateDir: stream){ if(!Files.isDirectory(stateDir)) continue; String name=stateDir.getFileName().toString();
                JSONObject cfg = readJson(stateDir.resolve("config.json"));
                Path movesPath = stateDir.resolve("moves.txt");
                Moves moves = Files.exists(movesPath)? new Moves(movesPath, H,W): null; // dims swapped earlier
                Graphics gfx = gfxFactory.load(stateDir.resolve("sprites"), cfg.optJSONObject("graphics")!=null?cfg.optJSONObject("graphics"):new JSONObject(), cellPx);
                Physics phys = physFactory.create(new Moves.Pair(0,0), name, cfg.optJSONObject("physics")!=null?cfg.optJSONObject("physics"):new JSONObject());
                State st=new State(moves,gfx,phys); st.name=name; states.put(name, st);
            }
        }
        // ─── apply per-piece transitions.csv overrides ───────────────
        Path transCsv = pieceDir.resolve("transitions.csv");
        if (Files.exists(transCsv)) {
            List<String> lines = Files.readAllLines(transCsv);
            for (String line : lines) {
                String l = line.strip();
                if (l.isEmpty() || l.startsWith("#") || l.toLowerCase().startsWith("from_state")) continue;
                String[] parts = l.split(",");
                if (parts.length < 3) continue;
                String frm = parts[0].trim();
                String event = parts[1].trim().toLowerCase();
                String nxt = parts[2].trim();
                State src = states.get(frm);
                State dst = states.get(nxt);
                if (src != null && dst != null) {
                    src.setTransition(event, dst);
                }
            }
        }

        // fallback: basic idle transitions if none provided
        State idle = states.get("idle");
        if (idle != null && idle.getTransitions().isEmpty()) {
            if (states.containsKey("move")) idle.setTransition("move", states.get("move"));
            if (states.containsKey("jump")) idle.setTransition("jump", states.get("jump"));
        }

        return idle;
    }

    private static JSONObject readJson(Path p){ try{ if(Files.exists(p)) return new JSONObject(Files.readString(p)); }catch(Exception ignored){} return new JSONObject(); }

    public Piece createPiece(String code, Moves.Pair cell){ State tmpl = templates.get(code); if(tmpl==null) throw new IllegalArgumentException("Unknown piece type "+code); // clone
        State idleClone = cloneStateMachine(tmpl, cell);
        Piece piece=new Piece(code+"_"+cell, idleClone); piece.reset(0); idleClone.reset(new Command(0,piece.id,"idle", List.of(cell))); return piece; }

    private State cloneStateMachine(State templateIdle, Moves.Pair cell){ Map<State, State> map=new HashMap<>(); Deque<State> stack=new ArrayDeque<>(); stack.push(templateIdle);
        while(!stack.isEmpty()){ State orig=stack.pop(); if(map.containsKey(orig)) continue; State copy=new State(orig.moves, orig.graphics, physFactory.create(cell, orig.name,new JSONObject())); copy.name=orig.name; map.put(orig, copy); stack.addAll(orig.getTransitions().values()); }
        // reconnect
        for(Map.Entry<State,State> e: map.entrySet()){ State orig=e.getKey(); State copy=e.getValue(); for(Map.Entry<String,State> tr: orig.getTransitions().entrySet()){ copy.setTransition(tr.getKey(), map.get(tr.getValue())); } }
        return map.get(templateIdle);
    }
} 