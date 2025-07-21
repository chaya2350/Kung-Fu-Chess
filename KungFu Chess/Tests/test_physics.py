# test_physics.py

import pytest
from Physics import Physics
from Command import Command


class MockBoard:
    def __init__(self, cell_W_pix=50, cell_H_pix=50):
        self.cell_W_pix = cell_W_pix
        self.cell_H_pix = cell_H_pix


def test_init_sets_start_and_end_cell():
    board = MockBoard()
    p = Physics((2, 3), board)
    assert p.start_cell == (2, 3)
    assert p.end_cell == (2, 3)
    assert p.get_pos() == (3 * board.cell_W_pix, 2 * board.cell_H_pix)


def test_reset_with_jump():
    board = MockBoard()
    p = Physics((1, 1), board)
    cmd = Command(timestamp=1000, piece_id="P1", type="Jump", params=[(3, 4)])
    p.reset(cmd)

    assert p.mode == "Jump"
    assert p.start_cell == (1, 1)
    assert p.end_cell == (3, 4)
    assert p.start_ms == 1000


def test_reset_idle_does_not_change_position():
    board = MockBoard()
    p = Physics((1, 2), board)         # set start_cell to (1, 2)
    p.end_cell = (1, 2)                # simulate previous position
    cmd = Command(timestamp=2000, piece_id="P1", type="Idle", params=[])
    p.reset(cmd)
    assert p.start_cell == (1, 2)
    assert p.end_cell == (1, 2)


def test_update_jump_and_arrival():
    board = MockBoard()
    p = Physics((0, 0), board)
    cmd = Command(timestamp=0, piece_id="P1", type="Jump", params=[(1, 1)])
    p.reset(cmd)

    # halfway jump (t = 0.5)
    result = p.update(150)
    assert result is None
    x, y = p.curr_px
    assert isinstance(x, int)
    assert isinstance(y, int)

    # complete jump
    result = p.update(400)
    assert isinstance(result, Command)
    assert result.type == "Arrived"
    assert p.start_cell == p.end_cell


def test_update_no_movement_returns_none():
    board = MockBoard()
    p = Physics((5, 5), board)
    result = p.update(now_ms=1000)
    assert result is None
    assert not hasattr(p, "curr_px")


def test_helpers_capture_flags():
    board = MockBoard()
    p = Physics((1, 1), board)
    assert p.can_be_captured()
    assert p.can_capture()
