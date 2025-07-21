# tests/test_fsm_and_physics.py
"""
Integration tests for Piece FSM + Physics + cooldown logic.

All assets are stubbed: no PNGs, no real board image, no OpenCV.
"""
import pytest
from pytest import approx
from collections import defaultdict

from Command  import Command
from Physics  import Physics
from State    import State
from Piece    import Piece
from Game import Game
Game._validate = lambda self, pieces: True

# ─────────────────────────── stubs ──────────────────────────────────────────
class DummyGraphics:
    def __init__(self): self.reset_calls = 0
    def reset(self, cmd): self.reset_calls += 1
    def update(self, now): pass
    def get_img(self):     return None
    def copy(self):        return DummyGraphics()

class DummyMoves:
    """offsets is a list[(dr, dc)] relative moves allowed from any square"""
    def __init__(self, offsets, board_size): self.offsets, self.board = offsets, board_size
    def get_moves(self, r, c):
        H, W = self.board
        return {(r+dr, c+dc)
                for dr, dc in self.offsets
                if 0 <= r+dr < H and 0 <= c+dc < W}

class DummyBoard:
    def __init__(self, cells=8, pix=70):
        self.W_cells = self.H_cells = cells
        self.cell_W_pix = self.cell_H_pix = pix
        self.img = None

# helper to build a full FSM piece ------------------------------------------------
def build_test_piece(cell=(6, 0), move_offset=( -1, 0 )):
    """
    idle  --Move-->  move        --Arrived-->  long_rest  --Arrived--> idle
    idle  --Jump-->  jump        --Arrived-->  short_rest --Arrived--> idle
    """
    board   = DummyBoard()
    boardSz = (board.H_cells, board.W_cells)
    graphics = DummyGraphics()

    idle_moves   = DummyMoves([(0,0)], boardSz)
    move_moves   = DummyMoves([move_offset], boardSz)
    jump_moves   = DummyMoves([(0,0)], boardSz)

    shared_phys = Physics(cell, board)          # ONE physics per piece

    idle       = State(idle_moves , graphics.copy(), shared_phys); idle.name = "idle"
    move       = State(move_moves , graphics.copy(), shared_phys); move.name = "move"
    jump       = State(jump_moves , graphics.copy(), shared_phys); jump.name = "jump"
    short_rest = State(jump_moves , graphics.copy(), shared_phys); short_rest.name = "short_rest"
    long_rest  = State(jump_moves , graphics.copy(), shared_phys); long_rest.name = "long_rest"

    # external transitions
    idle.set_transition("Move",  move)
    idle.set_transition("Jump",  jump)

    # internal transitions driven by Arrived
    move.set_transition("Arrived",  long_rest)
    jump.set_transition("Arrived",  short_rest)
    long_rest.set_transition("Arrived", idle)
    short_rest.set_transition("Arrived", idle)

    return Piece("PX_%s"%str(cell), idle), board

# ─────────────────────────── tests ───────────────────────────────────────────
def advance(piece, ms_from, ms_to, step=50):
    """call piece.update from ms_from→ms_to in increments; return final now"""
    t = ms_from
    while t < ms_to:
        t += step
        piece.update(t)
    return t

def test_move_full_cycle():
    piece, _ = build_test_piece()
    src = (6,0); dest = (5,0)

    # 1. issue Move
    cmd_move = Command(0, piece.id, "Move", [dest])
    piece.on_command(cmd_move, 0)
    assert piece.state.name == "move"

    # 2. simulate travel (>= duration_ms so Arrived fires)
    t = advance(piece, 0, piece.state.physics.duration_ms+10)
    assert piece.state.name == "long_rest"

    # cooldown should start *now*
    assert piece.state.cooldown_end_ms == approx(t + 6000, abs=50)

    # 3. midway through rest no external Move allowed
    cmd_fail = Command(t+1000, piece.id, "Move", [dest])
    piece.on_command(cmd_fail, t+1000)
    assert piece.state.name == "long_rest"           # unchanged

    # 4. after 6 s rest auto-Arrived → idle
    advance(piece, t, t+6000+10)
    assert piece.state.name == "idle"

def test_jump_full_cycle():
    piece, _ = build_test_piece()
    src = (6,0)

    # Jump on same square
    cmd_jump = Command(0, piece.id, "Jump", [src])
    piece.on_command(cmd_jump, 0)
    assert piece.state.name == "jump"

    # travel (duration_ms) – here distance==0 so duration==200 ms
    t = advance(piece, 0, 250)
    assert piece.state.name == "short_rest"
    assert piece.state.cooldown_end_ms == approx(t + 3000, abs=50)

    # finish rest
    advance(piece, t, t+3000+10)
    assert piece.state.name == "idle"

def test_no_idle_arrived_spam():
    piece, _ = build_test_piece()
    logs = defaultdict(int)

    # monkey-patch piece.state.physics.update to count Arrived
    orig_update = piece.state.physics.update
    def counting_update(now):
        cmd = orig_update(now)
        if cmd and cmd.type == "Arrived" and piece.state.name == "idle":
            logs["idle_arrived"] += 1
        return cmd
    piece.state.physics.update = counting_update

    # advance 10 seconds with no commands
    advance(piece, 0, 10000)
    assert logs["idle_arrived"] == 0, "Idle state should not emit Arrived repeatedly"

def test_rook_blocked_clear_path():
    board = DummyBoard()
    rook, _ = build_test_piece(cell=(7, 0), move_offset=(-1, 0))
    pawn, _ = build_test_piece(cell=(5, 0))
    game = Game([rook, pawn], board)

    # build the occupancy map manually (row, col) → Piece
    game.pos = {(7, 0): rook, (5, 0): pawn}

    # full-rank move should be rejected because path is blocked
    cmd = Command(0, rook.id, "Move", [(2, 0)])
    game._process_input(cmd)

    assert rook.state.name == "idle", "Rook should be blocked by pawn"



