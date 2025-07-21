import pytest
from unittest.mock import MagicMock
from Command import Command
from Board import Board
from Game import Game, InvalidBoard

# Dummy components

class DummyPhysics:
    def __init__(self, cell):
        self.start_cell = cell
        self.start_ms = 0

    def can_be_captured(self):
        return True

class DummyMoves:
    def __init__(self, legal_moves): self.legal_moves = legal_moves
    def get_moves(self, y, x): return self.legal_moves

class DummyState:
    def __init__(self, cell, can_transition=True, legal_moves=None):
        self.physics = DummyPhysics(cell)
        self._can_transition = can_transition
        self.cooldown_end_ms = 0
        self.moves = DummyMoves(legal_moves or [])  # ✅ Add this line

    def can_transition(self, now_ms):
        return self._can_transition

    def reset(self, cmd):
        self.physics.start_cell = cmd.params[0]
        self.physics.start_ms = cmd.timestamp

    def get_state_after_command(self, cmd, now_ms):
        return self

class DummyPiece:
    def __init__(self, id, cell, legal_moves=None):
        self.id = id
        self.state = DummyState(cell, legal_moves=legal_moves or [])
        self._moves = legal_moves or []

    def reset(self, ms): pass
    def update(self, ms): pass
    def draw_on_board(self, board, now_ms): pass

    class moves:
        @staticmethod
        def get_moves(y, x): return [(y+1, x+1)]

# Create a fake board
def make_board():
    mock_img = MagicMock()
    mock_img.img = MagicMock()
    return Board(100, 100, 8, 8, mock_img)


### Tests

def test_invalid_duplicate_piece_positions():
    board = make_board()
    p1 = DummyPiece("KW_a", (0, 0))
    p2 = DummyPiece("KB_b", (0, 0))  # duplicate cell
    with pytest.raises(InvalidBoard):
        Game([p1, p2], board)

def test_invalid_missing_king():
    board = make_board()
    p1 = DummyPiece("PW_x", (1, 1))
    with pytest.raises(InvalidBoard):
        Game([p1], board)

def test_valid_initialization():
    board = make_board()
    p1 = DummyPiece("KW_a", (0, 0))
    p2 = DummyPiece("KB_b", (7, 7))
    game = Game([p1, p2], board)
    assert isinstance(game, Game)

def test_game_time_ms_is_non_negative():
    board = make_board()
    g = Game([DummyPiece("KW_x", (0, 0)), DummyPiece("KB_y", (7, 7))], board)
    assert g.game_time_ms() >= 0

def test_valid_command_executes():
    board = make_board()
    piece = DummyPiece("KW_a", (0, 0), legal_moves=[(1, 1)])  # ✅ Allow (1,1)
    piece.state._can_transition = True
    game = Game([piece, DummyPiece("KB_b", (7, 7))], board)
    game.pos = {}
    game.piece_by_id["KW_a"] = piece
    cmd = Command(timestamp=500, piece_id="KW_a", type="Move", params=[(1, 1)])
    game._process_input(cmd)
    assert piece.state.physics.start_cell == (1, 1)


def test_invalid_command_blocked_by_cooldown():
    board = make_board()
    piece = DummyPiece("KW_a", (0, 0))
    piece.state._can_transition = False
    game = Game([piece, DummyPiece("KB_b", (7, 7))], board)
    game.pos = {}
    game.piece_by_id["KW_a"] = piece
    cmd = Command(timestamp=500, piece_id="KW_a", type="Move", params=[(1, 1)])
    game._process_input(cmd)
    assert piece.state.physics.start_cell == (0, 0)  # unchanged

def test_command_blocked_by_friendly_occupancy():
    board = make_board()
    p1 = DummyPiece("KW_a", (0, 0))
    p2 = DummyPiece("PW_a", (1, 1))
    game = Game([p1, p2, DummyPiece("KB_b", (7, 7))], board)
    game.pos = {(1, 1): p2}
    cmd = Command(timestamp=100, piece_id="KW_a", type="Move", params=[(1, 1)])
    game._process_input(cmd)
    assert p1.state.physics.start_cell == (0, 0)

def test_win_condition_triggers_correctly():
    board = make_board()
    g = Game([DummyPiece("KW_a", (0, 0)), DummyPiece("KB_b", (1, 1))], board)
    g.pieces = [p for p in g.pieces if not p.id.startswith("KB")]  # remove black king
    assert g._is_win() is True


def test_win_condition_false_when_both_kings_alive():
    board = make_board()
    g = Game([DummyPiece("KW_a", (0, 0)), DummyPiece("KB_b", (7, 7))], board)
    assert g._is_win() is False
