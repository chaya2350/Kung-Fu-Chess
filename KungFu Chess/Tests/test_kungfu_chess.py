# test_kungfu_logic.py

import pytest
from types import SimpleNamespace as NS

# ─── import your modules ────────────────────────────────────────────────
from Moves   import Moves
from Physics import Physics
from State   import State
from Command import Command
from Piece   import Piece
from Board   import Board
from Game    import Game

# ─── dummy graphics & image (we only test logic) ────────────────────────
class DummyImg:
    def __init__(self): self.img = None
class DummyGraphics:
    def __init__(self): pass
    def reset(self, *_): pass
    def update(self, *_): pass
    def get_img(self): return DummyImg()

# ─── helper to build a single‐state piece with custom offsets ────────────
def make_piece(pid, start_cell, rel_moves, board):
    # 1×1 px cells, 8×8 board
    moves = Moves.__new__(Moves)
    moves.rel_moves = rel_moves
    moves.W, moves.H = board.W_cells, board.H_cells

    phys    = Physics(start_cell, board)
    gfx     = DummyGraphics()
    state   = State(moves, gfx, phys)
    return Piece(pid, state)

# ─── fixtures ───────────────────────────────────────────────────────────
@pytest.fixture
def board():
    # cell size unused by logic tests, just needs the board dims
    return Board(cell_H_pix=1, cell_W_pix=1, W_cells=8, H_cells=8, img=DummyImg())

# ─── Tests for Moves ─────────────────────────────────────────────────────
def test_moves_within_bounds(board):
    m = Moves.__new__(Moves)
    m.rel_moves = [ (1,0), (0,1), (-1,-1), (7,7), (-8,0) ]
    m.W, m.H = board.W_cells, board.H_cells

    # from (0,0) only (1,0) and (0,1) are valid
    assert sorted(m.get_moves(0, 0)) == [(0,1),(1,0),(7,7)]

    # from (7,7) only (-1,-1) is valid
    assert m.get_moves(7, 7) == [(6,6)]

# ─── Tests for State cooldown logic ──────────────────────────────────────
def test_state_cooldown_move(board):
    # build a dummy state
    p = make_piece("P", (0,0), [], board)
    st = p.state
    t0 = 1000

    # Move → 6000 ms lock
    cmd = Command(t0, "P", "Move", [(1,1)])
    st.reset(cmd)
    assert st.cooldown_end_ms == t0 + 6000

    assert not st.can_transition(t0 + 5999)
    assert     st.can_transition(t0 + 6000)

def test_state_cooldown_jump(board):
    p = make_piece("P", (0,0), [], board)
    st = p.state
    t0 = 2000

    # Jump → 3000 ms lock
    cmd = Command(t0, "P", "Jump", [(0,0)])
    st.reset(cmd)
    assert st.cooldown_end_ms == t0 + 3000

    assert not st.can_transition(t0 + 2999)
    assert     st.can_transition(t0 + 3000)

# ─── Tests for Physics reset & simple teleport ───────────────────────────
def test_physics_reset_updates_cells(board):
    phys = Physics((2,3), board)
    t0   = 1500
    cmd  = Command(t0, "X", "Move", [(5,6)])
    phys.reset(cmd)
    # start_cell moves to old end_cell (defaults same), end_cell set to cmd.param
    assert phys.end_cell == (5,6)
    assert phys.start_ms   == t0

# ─── Tests for capture resolution ────────────────────────────────────────
def test_capture_latest_wins(board, monkeypatch):
    # create two pieces landing on same cell
    p1 = make_piece("A", (0,0), [], board)
    p2 = make_piece("B", (0,0), [], board)

    # simulate their move timestamps
    cmd1 = Command(100, "A", "Move", [(1,1)])
    cmd2 = Command(200, "B", "Move", [(1,1)])
    p1.state.reset(cmd1)
    p2.state.reset(cmd2)
    p1.state.physics.start_cell = (1,1)
    p2.state.physics.start_cell = (1,1)

    # bypass validate so we can inject directly
    monkeypatch.setattr(Game, "_validate", lambda self, pcs: True)
    g = Game([p1, p2], board)
    g._resolve_collisions()
    remaining = {p.id for p in g.pieces}
    assert remaining == {"B"}   # B arrived later, so A is removed

# ─── Tests for move rejection: illegal offset ────────────────────────────
def test_illegal_move_rejected(board, monkeypatch):
    p = make_piece("P", (1, 1), [(1, 0)], board)  # only (2,1) allowed
    monkeypatch.setattr(Game, "_validate", lambda self, pcs: True)
    g = Game([p, make_piece("KW_x", (0,0), [], board), make_piece("KB_y", (7,7), [], board)], board)
    g.pos = {}  # no blockers
    g.piece_by_id["P"] = p
    t0 = 1000
    cmd = Command(t0, "P", "Move", [(0, 0)])  # invalid move
    g._process_input(cmd)
    assert p.state.physics.start_cell == (1, 1)

# ─── Friendly fire block ─────────────────────────────────────────────────
def test_friendly_block_rejected(board, monkeypatch):
    p1 = make_piece("PW_1", (1, 1), [(1, 0)], board)
    p2 = make_piece("PW_2", (2, 1), [], board)
    monkeypatch.setattr(Game, "_validate", lambda self, pcs: True)
    g = Game([p1, p2, make_piece("KW_x", (0,0), [], board), make_piece("KB_y", (7,7), [], board)], board)
    g.pos = {(2, 1): p2}
    g.piece_by_id["PW_1"] = p1
    t0 = 2000
    cmd = Command(t0, "PW_1", "Move", [(2, 1)])  # valid offset, but friendly blocked
    g._process_input(cmd)
    assert p1.state.physics.start_cell == (1, 1)

# ─── Jump moves apply correctly ──────────────────────────────────────────
def test_jump_moves_update_physics(board, monkeypatch):
    p = make_piece("P", (3, 3), [(2, 0)], board)
    monkeypatch.setattr(Game, "_validate", lambda self, pcs: True)
    g = Game([p, make_piece("KW_x", (0,0), [], board), make_piece("KB_y", (7,7), [], board)], board)
    g.pos = {}
    g.piece_by_id["P"] = p
    t0 = 3000
    cmd = Command(t0, "P", "Jump", [(5, 3)])  # legal jump
    g._process_input(cmd)
    assert p.state.physics.start_cell == (5, 3)

# ─── Capture logic: tie-breaker favors later timestamp ───────────────────
def test_capture_conflict_resolves_to_later(board, monkeypatch):
    p1 = make_piece("A", (4, 4), [], board)
    p2 = make_piece("B", (4, 4), [], board)
    cmd1 = Command(111, "A", "Move", [(2,2)])
    cmd2 = Command(222, "B", "Move", [(2,2)])
    p1.state.reset(cmd1)
    p2.state.reset(cmd2)
    p1.state.physics.start_cell = (2,2)
    p2.state.physics.start_cell = (2,2)
    monkeypatch.setattr(Game, "_validate", lambda self, pcs: True)
    g = Game([p1, p2, make_piece("KW_x", (0,0), [], board), make_piece("KB_y", (7,7), [], board)], board)
    g._resolve_collisions()
    assert {p.id for p in g.pieces} == {"B", "KW_x", "KB_y"}

# ─── Win detection with king removed ─────────────────────────────────────
def test_win_triggered_when_king_is_taken(board, monkeypatch):
    kw = make_piece("KW_x", (0,0), [], board)
    kb = make_piece("KB_y", (7,7), [], board)
    #monkeypatch.setattr(Game, "_validate", lambda self, pcs: True)
    g = Game([kw, kb], board)
    g.pieces = [kw]  # simulate KB has been captured
    assert g._is_win()

