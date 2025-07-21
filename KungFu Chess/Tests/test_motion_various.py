# tests/test_motion_various.py
import numpy as np
from unittest.mock import patch
import pytest

from Command import Command
from Physics import Physics
import img as img_mod          # we’ll monkey-patch img_mod.Img


# ─── recording stub for Img ────────────────────────────────────────────────
class RecordingImg(img_mod.Img):
    """Drop-in replacement that only records draw_on() calls."""
    def __init__(self):
        super().__init__()
        self.traj = []                         # [(x, y), …]

    def read(self, *a, **kw):                  # skip disk I/O, keep chainable
        return self

    def draw_on(self, other, x, y):            # record, no real blending
        self.traj.append((x, y))


# ─── tiny board stub ───────────────────────────────────────────────────────
class DummyBoard:
    def __init__(self, cell_pix: int = 70):
        self.cell_W_pix = cell_pix
        self.cell_H_pix = cell_pix


# ─── numeric helpers (≤ 1-pixel tolerance) ─────────────────────────────────
PIX_TOL = 1.0

def max_perp_distance(pts):
    """Largest perpendicular distance of pts from the end-to-end line."""
    p0, pN = pts[0], pts[-1]
    v = pN - p0
    norm = np.linalg.norm(v)
    if norm < 1e-9:
        return 0.0
    return np.max(np.abs(np.cross(v, pts - p0)) / norm)

def step_variation(pts):
    steps = np.linalg.norm(pts[1:] - pts[:-1], axis=1)
    return steps.max() - steps.min()


CASES = [
    ((1, 1), (6, 6)),   # long diagonal
    ((0, 0), (0, 7)),   # full rank
    ((7, 7), (0, 7)),   # full file
    ((2, 5), (5, 2)),   # anti-diagonal
    ((3, 0), (3, 4)),   # short horizontal
]
PIX_TOL_LINE  = 1.0   # max perpendicular distance from ideal line
PIX_TOL_STEP  = 2.0   # max range of successive step lengths


@pytest.mark.parametrize(
    "start_cell,end_cell", CASES,
    ids=[f"{s}->{e}" for s, e in CASES]
)

def test_move_straight_and_uniform(start_cell, end_cell):
    board = DummyBoard()
    phys  = Physics(start_cell, board)
    phys.reset(Command(0, "P?", "Move", [end_cell]))

    # patch img.Img → RecordingImg only inside this with-block
    with patch.object(img_mod, "Img", img_mod.Img):
        sprite, bg = img_mod.Img(), img_mod.Img()

        # sample physics every 30 ms up to 300 ms
        for t in range(0, 301, 30):
            phys.update(t)
            x, y = phys.curr_px
            sprite.draw_on(bg, x, y)

        pts = np.asarray(sprite.traj, dtype=float)
    print(pts)
    # straight line?
    assert max_perp_distance(pts) <= PIX_TOL_LINE, \
        f"{start_cell}->{end_cell}: deviates >{PIX_TOL_LINE} px from straight line"

    assert step_variation(pts) <= PIX_TOL_STEP, \
        f"{start_cell}->{end_cell}: step lengths vary by >{PIX_TOL_STEP} px"
