import pathlib, time

from Board import Board
from img import Img
from PieceFactory import PieceFactory
from GraphicsFactory import GraphicsFactory, MockImgFactory
from Game import Game
from Command import Command
from GameFactory import create_game

import numpy as np

import pytest

PIECES_ROOT = pathlib.Path(__file__).parent.parent / "pieces"
BOARD_CSV = PIECES_ROOT / "board.csv"


def _blank_board():
    cell_px = 32
    img = Img();
    img.img = np.zeros((cell_px * 8, cell_px * 8, 4), dtype=np.uint8)
    return Board(cell_px, cell_px, 8, 8, img)


# interface image_loader
# real_loader: image_loader
# fake_loader: image_loader

def test_game_move_and_capture():
    game = create_game("../pieces", MockImgFactory())
    game._time_factor = 1000000000
    game._update_cell2piece_map()
    pw = game.pos[(6, 0)][0]
    pb = game.pos[(1, 1)][0]
    game.user_input_queue.put(Command(game.game_time_ms(), pw.id, "move", [(6, 0), (4, 0)]))
    game.user_input_queue.put(Command(game.game_time_ms(), pb.id, "move", [(1, 1), (3, 1)]))
    game.run(timeout=2, is_with_graphics=False)
    assert pw.current_cell() == (4, 0)
    assert pb.current_cell() == (3, 1)
    game._run_game_loop(timeout=8, is_with_graphics=False)
    game.user_input_queue.put(Command(game.game_time_ms(), pw.id, "move", [(4, 0), (3, 1)]))
    game._run_game_loop(timeout=5, is_with_graphics=False)
    assert pw.current_cell() == (3, 1)
    assert pw in game.pieces
    assert pb not in game.pieces

