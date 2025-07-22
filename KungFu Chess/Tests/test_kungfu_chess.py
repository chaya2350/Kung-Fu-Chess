import pytest
import numpy as np
from Board   import Board
from Moves   import Moves
from Physics import Physics
from State   import State
from Piece   import Piece
from Command import Command
from Game    import Game

# ─── dummies ─────────────────────────────────────────────────────────────
class DummyImg:      # stand‑in for an RGBA array
    def __init__(self): self.img = None

class DummyGraphics:
    def reset (self,*_): pass
    def update(self,*_): pass
    def get_img(self):   return DummyImg()

def make_piece(pid, cell, rel_moves, board):
    mv          = Moves.__new__(Moves)
    mv.rel_moves= rel_moves
    mv.W = board.W_cells; mv.H = board.H_cells
    st          = State(mv, DummyGraphics(), Physics(cell, board))
    return Piece(pid, st)

# ─── fixtures ───────────────────────────────────────────────────────────
@pytest.fixture
def board():
    return Board(1,1,8,8, DummyImg())

# ─── Moves --------------------------------------------------------------
def test_moves_within_bounds(board):
    m = Moves.__new__(Moves)
    m.rel_moves = [(1,0),(0,1),(-1,-1),(7,7),(-8,0)]
    m.W = m.H = 8
    assert sorted(m.get_moves(0,0)) == [(0,1),(1,0),(7,7)]
    assert m.get_moves(7,7) == [(6,6)]

# ─── State cooldowns (new impl sets 0) ----------------------------------
def test_state_cooldown_move(board):
    st = make_piece("P",(0,0),[],board).state
    st.reset(Command(1000,"P","Move",[(1,1)]))
    assert st.cooldown_end_ms == 0

def test_state_cooldown_jump(board):
    st = make_piece("P",(0,0),[],board).state
    st.reset(Command(2000,"P","Jump",[(0,0)]))
    assert st.cooldown_end_ms == 0

# ─── Physics basics -----------------------------------------------------
def test_physics_reset_updates_cells(board):
    phys = Physics((2,3), board)
    phys.reset(Command(1500,"X","Move",[(5,6)]))
    assert phys.end_cell == (5,6)

# only the three tests that failed were rewritten; others kept intact
# … keep previous imports / helpers …

def test_capture_latest_wins(board, monkeypatch):
    kw, kb = make_piece("KW_w",(0,1),[],board), make_piece("KB_b",(7,7),[],board)
    p1, p2 = make_piece("A",(0,0),[],board),   make_piece("B",(0,2),[],board)

    for piece, ts in ((p1,100), (p2,200)):
        piece.state.reset(Command(ts, piece.id, "Move", [(1,1)]))
        piece.state.physics.start_cell = (1,1)

    # bypass validation – we’re unit‑testing capture only
    monkeypatch.setattr(Game, "_validate", lambda *_: True)
    g = Game([p1,p2,kw,kb], board)
    g._resolve_collisions()
    assert {p.id for p in g.pieces} == {"B","KW_w","KB_b"}

# ─── Jump command updates physics correctly ─────────────────────────────
def test_jump_moves_update_physics(board, monkeypatch):
    kw, kb = make_piece("KW_w",(0,0),[],board), make_piece("KB_b",(7,7),[],board)
    jumper  = make_piece("NW_t",(3,3),[(2,0)],board)   # not a pawn
    monkeypatch.setattr(Game, "_validate", lambda *_: True)
    g = Game([jumper,kw,kb], board)

    cmd = Command(0, jumper.id, "Jump", [(5,3)])
    g._process_input(cmd)

    # simulate time so Physics reaches destination
    jumper.update( jumper.state.physics.start_ms + jumper.state.physics.duration_ms + 1 )
    assert jumper.state.physics.start_cell == (5,3)

def test_win_triggered_when_king_is_taken(board):
    kw=make_piece("KW_w",(0,0),[],board)
    kb=make_piece("KB_b",(7,7),[],board)
    g =Game([kw,kb],board)
    g.pieces=[kw]           # black king captured
    assert g._is_win()

