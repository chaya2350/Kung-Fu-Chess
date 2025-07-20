
import logging
import pathlib

from Board import Board
from Game import Game
from PieceFactory import PieceFactory
from img import Img


def create_board() -> Board:
    board_img = Img().read(
        pathlib.Path(__file__).parent / "board.png",
        size=(560, 560),  # width, height
        keep_aspect=False  # stretch to fit exactly
    )
    return Board(70, 70, 8, 8, board_img)   # 8×8 chessboard, 70 px tiles

# ───────────────────────────── demo ─────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    board = create_board()

    # Produce one dummy white-pawn at A2
    pf = PieceFactory(board)
    pf.generate_library(pathlib.Path(__file__).parent / "pieces")
    initial_setup = {
        "RW": [(7, 0), (7, 7)], "RB": [(0, 0), (0, 7)],
        "NW": [(7, 1), (7, 6)], "NB": [(0, 1), (0, 6)],
        "BW": [(7, 2), (7, 5)], "BB": [(0, 2), (0, 5)],
        "QW": (7, 3), "QB": (0, 3),
        "KW": (7, 4), "KB": (0, 4),
        "PW": [(6, c) for c in range(8)],
        "PB": [(1, c) for c in range(8)],
    }

    pieces = []
    for code, cells in initial_setup.items():
        if isinstance(cells, tuple):  # single square
            cells = [cells]
        for cell in cells:
            pieces.append(pf.create_piece(code, cell))
    print("Pieces on board:", [p.id for p in pieces])
    Game(pieces, board).run()

