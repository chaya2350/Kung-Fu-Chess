# tests/test_piece_actions.py
import pytest
from collections import namedtuple
import numpy as np

from Physics import Physics
from State   import State
from Piece   import Piece
from Command import Command

# --- stub helpers ---------------------------------------------------------
class StubMoves:
    """Simple Moves substitute: supports get_moves(row, col)."""
    def __init__(self, offsets, board_size):
        self.offsets   = offsets            # list[(dr, dc)]
        self.board_H, self.board_W = board_size

    def get_moves(self, r, c):
        moves = set()
        for dr, dc in self.offsets:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.board_H and 0 <= nc < self.board_W:
                moves.add((nr, nc))
        return moves


class DummyGraphics:
    def reset(self, cmd):  pass
    def update(self, now): pass
    def get_img(self):     return None


class DummyBoard:
    def __init__(self, w_cells=8, h_cells=8, pix=70):
        self.W_cells, self.H_cells = w_cells, h_cells
        self.cell_W_pix = self.cell_H_pix = pix
        self.img = None   # not needed here


# -------------------------------------------------------------------------
def build_piece(cell=(1, 1)):
    """Return a Piece with idle→move/jump state machine using stub moves."""
    board = DummyBoard()
    board_size = (board.H_cells, board.W_cells)

    # movesets
    idle_moves  = StubMoves([(0, 0)], board_size)     # stay
    move_moves  = StubMoves([(0, 1)], board_size)     # one step right
    jump_moves  = StubMoves([(0, 0)], board_size)     # no-offset jump

    # physics
    idle_phys  = Physics(cell, board)
    move_phys  = Physics(cell, board)
    jump_phys  = Physics(cell, board)

    # graphics (dummy)
    g = DummyGraphics()

    # states
    idle = State(idle_moves,  g, idle_phys);  idle.name = "idle"
    move = State(move_moves,  g, move_phys);  move.name = "move"
    jump = State(jump_moves,  g, jump_phys);  jump.name = "jump"

    # transitions
    idle.set_transition("Move",  move)
    idle.set_transition("Jump",  jump)
    move.set_transition("Arrived", idle)
    jump.set_transition("Arrived", idle)

    return Piece("PX_(1,1)", idle)


# -------------------------------------------------------------------------
def test_jump_and_move_legality():
    piece = build_piece()
    src   = (1, 1)

    # --- 1. Jump ----------------------------------------------------------
    cmd_jump = Command(100, piece.id, "Jump", [src])   # dest = same square
    piece.on_command(cmd_jump, new_ms=100)

    assert piece.state.name == "jump"
    assert piece.state.moves.get_moves(*src) == {src}, \
        "Jump state should allow only staying in place"

    # simulate arrival so we can issue next command
    piece.update( piece.state.physics.start_ms + 1000 )

    # --- 2. Move ----------------------------------------------------------
    dest = (1, 2)         # one square right
    cmd_move = Command(2000, piece.id, "Move", [dest])
    piece.on_command(cmd_move, now_ms=2000)

    assert piece.state.name == "move"
    legal_moves = piece.state.moves.get_moves(*src)
    assert dest in legal_moves, \
        f"Move destination {dest} not found in legal moves {legal_moves}"
