# tests/test_straight_line.py
import math
import numpy as np
import pytest

from Physics import Physics
from Command import Command


# ──── helpers ──────────────────────────────────────────────────────────────
class DummyBoard:
    """Minimal board stub with pixel sizes only (no rendering needed)."""
    def __init__(self, cell_pix: int = 70):
        self.cell_W_pix = cell_pix
        self.cell_H_pix = cell_pix


TOL = 1e-5


def all_collinear(points, tol=TOL) -> bool:
    """Return True iff every point lies on the line p0-p1 within `tol`."""
    if len(points) < 3:
        return True
    p0, p1 = points[0], points[1]
    direction = p1 - p0
    for p in points[2:]:
        # 2-D cross-product z-component = 0  → collinear
        if abs(np.cross(direction, p - p0)) > tol:
            return False
    return True


def equally_spaced(points, tol=TOL) -> bool:
    """True if successive |pi+1 − pi| differ by ≤ tol."""
    steps = [np.linalg.norm(points[i + 1] - points[i])
             for i in range(len(points) - 1)]
    return max(steps) - min(steps) <= tol


# ──── actual test ──────────────────────────────────────────────────────────
def test_straight_uniform_motion():
    board = DummyBoard(cell_pix=70)             # 8×8 chessboard tiles = 70 px
    start_cell = (1, 1)                         # A
    end_cell   = (6, 6)                         # B  (same diagonal)

    phys = Physics(start_cell, board)
    cmd  = Command(0, "PA", "Move", [end_cell])   # timestamp 0 ms
    phys.reset(cmd)

    # sample the trajectory every 30 ms (300 ms total in Physics.update)
    samples = []
    for t in range(0, 301, 30):                # 0 … 300 ms inclusive
        phys.update(t)
        samples.append(np.array(phys.curr_px, dtype=float))

    samples = np.stack(samples)                # shape (N, 2)

    assert all_collinear(samples),  "Path is not collinear"
    assert equally_spaced(samples, tol=6.0), "Steps are not uniformly spaced"
