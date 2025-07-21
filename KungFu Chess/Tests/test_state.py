# test_state.py

import pytest
from State import State
from Command import Command


class MockGraphics:
    def __init__(self):
        self.reset_called = False
        self.updated = False

    def reset(self, cmd):
        self.reset_called = True
        self.last_cmd = cmd

    def update(self, now_ms):
        self.updated = True


class MockPhysics:
    def __init__(self):
        self.start_ms = 0
        self.reset_called = False
        self.return_internal = None

    def reset(self, cmd):
        self.reset_called = True
        self.start_ms = cmd.timestamp

    def update(self, now_ms):
        return self.return_internal


class MockMoves:
    pass


def test_reset_sets_cooldown_move():
    g = MockGraphics()
    p = MockPhysics()
    s = State(moves=MockMoves(), graphics=g, physics=p)

    cmd = Command(timestamp=1000, piece_id="P1", type="Move", params=[(2, 3)])
    s.reset(cmd)

    assert g.reset_called
    assert p.reset_called
    assert s.cooldown_end_ms == 7000


def test_reset_sets_cooldown_jump():
    g = MockGraphics()
    p = MockPhysics()
    s = State(MockMoves(), g, p)

    cmd = Command(timestamp=2000, piece_id="P1", type="Jump", params=[(5, 5)])
    s.reset(cmd)

    assert s.cooldown_end_ms == 5000


def test_can_transition_true():
    s = State(MockMoves(), MockGraphics(), MockPhysics())
    s.cooldown_end_ms = 5000
    assert s.can_transition(now_ms=6000) is True


def test_can_transition_false():
    s = State(MockMoves(), MockGraphics(), MockPhysics())
    s.cooldown_end_ms = 8000
    assert s.can_transition(now_ms=7000) is False


def test_get_state_after_command_transitions_if_allowed():
    g = MockGraphics()
    p = MockPhysics()
    curr = State(MockMoves(), g, p)
    next_state = State(MockMoves(), MockGraphics(), MockPhysics())
    curr.set_transition("Move", next_state)

    curr.cooldown_end_ms = 0  # ensure transition is allowed
    cmd = Command(timestamp=1000, piece_id="P1", type="Move", params=[(1, 1)])

    new_state = curr.get_state_after_command(cmd, new_ms=2000)
    assert new_state == next_state
    assert new_state.physics.start_ms == 1000  # reset happened


def test_get_state_after_command_no_transition():
    g = MockGraphics()
    p = MockPhysics()
    curr = State(MockMoves(), g, p)

    cmd = Command(timestamp=1500, piece_id="P1", type="Move", params=[(3, 2)])
    curr.cooldown_end_ms = 0  # allow transition

    result = curr.get_state_after_command(cmd, new_ms=1600)
    assert result == curr
    assert p.reset_called


def test_update_with_internal_command():
    g = MockGraphics()
    p = MockPhysics()
    curr = State(MockMoves(), g, p)

    internal_cmd = Command(timestamp=3000, piece_id="P1", type="Jump", params=[])
    p.return_internal = internal_cmd

    # simulate state transition
    next_state = State(MockMoves(), MockGraphics(), MockPhysics())
    curr.set_transition("Jump", next_state)
    curr.cooldown_end_ms = 0

    result = curr.update(4000)
    assert result is next_state


def test_update_without_internal_command():
    g = MockGraphics()
    p = MockPhysics()
    p.return_internal = None

    s = State(MockMoves(), g, p)
    result = s.update(1234)

    assert result == s
    assert g.updated is True


def test_get_command_returns_idle():
    p = MockPhysics()
    p.start_ms = 4567
    s = State(MockMoves(), MockGraphics(), p)

    cmd = s.get_command()
    assert cmd.timestamp == 4567
    assert cmd.type == "Idle"
