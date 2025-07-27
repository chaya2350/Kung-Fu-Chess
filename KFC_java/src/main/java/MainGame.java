import java.nio.file.Path;import java.util.*;

public class MainGame {
    public static void main(String[] args) throws Exception {
        Board board = BoardFactory.loadDefault(Path.of("../pieces/board.png"));
        PieceFactory pf = new PieceFactory(board);
        pf.generateLibrary(Path.of("../pieces"));
        List<Piece> pieces = new ArrayList<>();
        // add kings only for demo
        pieces.add(pf.createPiece("KW", new Moves.Pair(7,4)));
        pieces.add(pf.createPiece("KB", new Moves.Pair(0,4)));
        Game game = new Game(pieces, board);
        game.run();
    }
} 