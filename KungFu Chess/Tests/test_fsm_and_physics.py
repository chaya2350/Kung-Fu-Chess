"""
Integration tests for Piece FSM + Physics + cooldown logic.
Assets are stubbed (no PNGs, no OpenCV), only pure logic is exercised.
"""
import pytest
from collections import defaultdict
from Command   import Command
from Physics   import Physics
from State     import State
from Piece     import Piece
from Board     import Board
from Game      import Game, InvalidBoard


# ── minimal stubs ────────────────────────────────────────────────────────
class DummyGraphics:
    def reset(self, *_):  ...
    def update(self, *_): ...
    def get_img(self):    return None

class DummyMoves:
    def __init__(self, rel, size, legal_moves=None):
        self.rel, self.W, self.H = rel, *size
        self.legal_moves = legal_moves or []

    def get_moves(self, r, c, *args, **kwargs):
        return [(r+dr, c+dc) for dr,dc in self.legal_moves]

class DummyBoard:
    def __init__(self, n=8): self.cell_H_pix=self.cell_W_pix=70; self.W_cells=self.H_cells=n

# ── helper to create one full state‑machine piece ───────────────────────
def build_test_piece(*, cell=(6,0), move_offset=(-1,0)):
    board   = DummyBoard()
    size    = (board.W_cells, board.H_cells)

    idleM   = DummyMoves([(0,0)], size)
    moveM   = DummyMoves([move_offset], size)
    jumpM   = DummyMoves([(0,0)], size)

    phys    = Physics(cell, board)

    idle       = State(idleM , DummyGraphics(), phys); idle.name="idle"
    move       = State(moveM , DummyGraphics(), phys); move.name="move"
    jump       = State(jumpM , DummyGraphics(), phys); jump.name="jump"
    long_rest  = State(jumpM , DummyGraphics(), phys); long_rest.name="long_rest"
    short_rest = State(jumpM , DummyGraphics(), phys); short_rest.name="short_rest"

    # external links
    idle .set_transition("Move", move)
    idle .set_transition("Jump", jump)
    # internal links
    move .set_transition("Arrived", long_rest)
    jump .set_transition("Arrived", short_rest)
    long_rest .set_transition("Arrived", idle)
    short_rest.set_transition("Arrived", idle)

    return Piece("PX_%s"%str(cell), idle), board

# ------------------------------------------------------------------------
def advance(piece, frm, to, step=50):
    t=frm
    while t<to:
        t+=step; piece.update(t)
    return t

def test_move_full_cycle():
    p,_ = build_test_piece()
    src=(6,0); dest=(5,0)
    cmd=Command(0,p.id,"Move",[dest]); p.on_command(cmd,0)
    assert p.state.name=="move"

    t=advance(p,0,p.state.physics.duration_ms+10)
    assert p.state.name=="long_rest"
    t=advance(p,t,t+6000+10)
    assert p.state.name=="idle"

def test_jump_full_cycle():
    p,_ = build_test_piece()
    cmd=Command(0,p.id,"Jump",[p.state.physics.start_cell])
    p.on_command(cmd,0)
    assert p.state.name=="jump"
    t=advance(p,0,250)
    assert p.state.name=="short_rest"
    advance(p,t,t+3000+10)
    assert p.state.name=="idle"

def test_no_idle_arrived_spam():
    p,_=build_test_piece()
    cnt=0
    for t in range(0,10_000,50):
        p.update(t)
        if p.state.name=="idle" and hasattr(p.state.physics,"wait_only") and p.state.physics.wait_only:
            cnt+=1
    assert cnt==0

def test_rook_blocked_clear_path():
    board=DummyBoard()
    rook,_=build_test_piece(cell=(7,0),move_offset=(-1,0))
    pawn,_=build_test_piece(cell=(5,0))
    # add kings so Game.validate passes
    kw,_  = build_test_piece(cell=(0,0)); kw.id="KW_stub"
    kb,_  = build_test_piece(cell=(7,7)); kb.id="KB_stub"
    game=Game([rook,pawn,kw,kb],board)

    cmd=Command(0,rook.id,"Move",[(2,0)])
    game._process_input(cmd)
    # should be rejected and stay idle
    assert rook.state.name=="idle"
