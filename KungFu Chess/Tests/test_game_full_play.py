import pathlib, time

from Board import Board
from img import Img
from PieceFactory import PieceFactory
from GraphicsFactory import GraphicsFactory, MockImgFactory
from Game import Game
from Command import Command

import numpy as np

import pytest


PIECES_ROOT = pathlib.Path(__file__).parent.parent / "pieces"
BOARD_CSV   = PIECES_ROOT / "board.csv"


def _blank_board():
    cell_px = 32
    img = Img(); img.img = np.zeros((cell_px*8, cell_px*8, 4), dtype=np.uint8)
    return Board(cell_px, cell_px, 8, 8, img)


def _load_game() -> Game:
    board = _blank_board()
    gfx_factory = GraphicsFactory(MockImgFactory())
    pf = PieceFactory(board, graphics_factory=gfx_factory)
    pf.generate_library(PIECES_ROOT)
    pieces = []
    with BOARD_CSV.open() as f:
        for r, line in enumerate(f):
            for c, code in enumerate(line.strip().split(",")):
                if code:
                    pieces.append(pf.create_piece(code, (r, c)))
    return Game(pieces, board)


@pytest.mark.xfail(reason="Full gameplay requires new create_game behaviour not yet implemented")
def test_game_move_and_capture():
    game = _load_game()

    # White pawn at (6,0) moves to (5,0)
    wp = next(p for p in game.pieces if p.id.startswith("PW_") and p.current_cell()==(6,0))
    # Must select first according to state machine
    cmd_sel = Command(game.game_time_ms(), wp.id, "select", [(6,0)])
    game._process_input(cmd_sel)

    cmd_move = Command(game.game_time_ms(), wp.id, "move", [(6,0),(5,0)])
    game._process_input(cmd_move)
    wp.update(wp.state.physics.get_start_ms() + 2000)  # advance time

    # Black pawn at (1,1) moves then captures white pawn
    bp = next(p for p in game.pieces if p.id.startswith("PB_") and p.current_cell()==(1,1))
    cmd_bp_sel = Command(game.game_time_ms(), bp.id, "select", [(1,1)])
    game._process_input(cmd_bp_sel)

    cmd_bp_move = Command(game.game_time_ms(), bp.id, "move", [(1,1),(2,1)])
    game._process_input(cmd_bp_move)
    bp.update(bp.state.physics.get_start_ms()+2000)

    # Now jump onto white pawn square to capture
    cmd_bp_sel2 = Command(game.game_time_ms(), bp.id, "select", [(2,1)])
    game._process_input(cmd_bp_sel2)

    cmd_bp_jump = Command(game.game_time_ms(), bp.id, "jump", [(2,1),(5,0)])
    game._process_input(cmd_bp_jump)
    bp.update(bp.state.physics.get_start_ms()+200)

    game._resolve_collisions()
    assert wp not in game.pieces  # pawn captured
    assert bp in game.pieces  # winner remains


@pytest.mark.xfail(reason="Awaiting GameFactory integration")
def test_game_win_condition():
    game = _load_game()
    # Remove Black king and verify win
    bk = next(p for p in game.pieces if p.id.startswith("KB_"))
    game.pieces.remove(bk)
    assert game._is_win() 