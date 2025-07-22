# tests/test_piece_actions.py
import pytest
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
        return {
            (nr, nc)
            for dr, dc in self.offsets
            if 0 <= (nr := r + dr) < self.board_H
            and 0 <= (nc := c + dc) < self.board_W
        }

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

    # physics: each state gets its own instance
    idle_phys = Physics(cell, board)
    move_phys = Physics(cell, board)
    jump_phys = Physics(cell, board)

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
def test_jump_then_move_is_blocked_until_rest_finishes():
    piece = build_piece()
    src = (1, 1)

    # Issue a Jump
    cmd_jump = Command(100, piece.id, "Jump", [src])
    piece.on_command(cmd_jump, now_ms=100)
    assert piece.state.name == "jump"

    # Advance to after the jump's arrival + short rest (duration_ms + cooldown)
    arrive = piece.state.physics.start_ms + piece.state.physics.duration_ms + 1
    piece.update(arrive)
    assert piece.state.name == "idle"
    # still in cooldown
    assert piece.state.cooldown_end_ms > arrive

    # Attempt Move during cooldown → still idle
    dest = (1, 2)
    t1 = arrive + 500
    piece.on_command(Command(t1, piece.id, "Move", [dest]), now_ms=t1)
    assert piece.state.name == "idle"

    # After cooldown expires, Move is accepted
    t2 = piece.state.cooldown_end_ms + 1
    piece.on_command(Command(t2, piece.id, "Move", [dest]), now_ms=t2)
    assert piece.state.name == "move"

def test_move_completion_transitions_back_to_idle():
    piece = build_piece()
    dest = (1, 2)

    # Issue Move
    piece.on_command(Command(0, piece.id, "Move", [dest]), now_ms=0)
    assert piece.state.name == "move"

    # Advance past move arrival
    arrive = piece.state.physics.start_ms + piece.state.physics.duration_ms + 1
    piece.update(arrive)
    assert piece.state.name == "idle"

def test_physics_traversal_is_linear_and_repeatable():
    board = DummyBoard(pix=10)
    phys = Physics((0,0), board)
    dest = (0, 1)
    phys.reset(Command(0, "X", "Move", [dest]))

    # ensure duration_ms is int
    dur = int(phys.duration_ms)
    step = max(1, dur // 5)
    samples = []
    for dt in range(0, dur + 1, step):
        phys.update(phys.start_ms + dt)
        samples.append(np.array(phys.curr_px, dtype=float))

    samples = np.stack(samples)
    diffs = np.diff(samples, axis=0)
    # verify uniform spacing: dx and dy increments all proportional
    ratios = diffs[:,0] / diffs[:,1]
    assert np.allclose(ratios, ratios[0], atol=1e-6)

def test_cooldown_blocks_reentry_until_arrival():
    piece = build_piece()
    dest = (1, 2)

    # First Move
    piece.on_command(Command(0, piece.id, "Move", [dest]), now_ms=0)
    assert piece.state.name == "move"

    # Try a second Move _before_ arrival → still in 'move'
    piece.on_command(Command(50, piece.id, "Move", [dest]), now_ms=50)
    assert piece.state.name == "move"

    # Now advance past arrival
    arrive = piece.state.physics.start_ms + piece.state.physics.duration_ms + 1
    piece.update(arrive)
    assert piece.state.name == "idle"

    # After arrival+cooldown, Move should be accepted again
    ok = piece.state.cooldown_end_ms + 1
    piece.on_command(Command(ok, piece.id, "Move", [dest]), now_ms=ok)
    assert piece.state.name == "move"
