import pathlib, tempfile
import numpy as np

from Board import Board
from Command import Command
from Graphics import Graphics
from GraphicsFactory import MockImgFactory
from Moves import Moves

PIECES_ROOT = pathlib.Path(__file__).parent.parent / "pieces"
SPRITES_DIR = PIECES_ROOT / "BB" / "states" / "idle" / "sprites"


def _blank_img():
    from mock_img import MockImg
    return MockImg()


def test_graphics_animation_timing():
    """Test frame advancement based on fps."""
    gfx = Graphics(sprites_folder=SPRITES_DIR,
                   cell_size=(32, 32),
                   loop=True,
                   fps=10.0,
                   img_loader=MockImgFactory())

    # Reset at t=0
    gfx.reset(Command(0, "test", "idle", []))
    assert gfx.cur_frame == 0
    num_frames = len(gfx.frames)
    frame_duration = 1000 / gfx.fps
    for i in range(num_frames):
        gfx.update(i * frame_duration + frame_duration / 2)
        assert gfx.cur_frame == i

    gfx.update(num_frames * frame_duration + frame_duration / 2)
    assert gfx.cur_frame == 0


def test_graphics_non_looping():
    """Test non-looping animation stays on last frame."""
    gfx = Graphics(sprites_folder=SPRITES_DIR,
                   cell_size=(32, 32),
                   loop=False,
                   fps=10.0,
                   img_loader=MockImgFactory())

    gfx.frames = [_blank_img() for _ in range(3)]
    gfx.reset(Command(0, "test", "idle", []))

    # Advance well past end of animation
    gfx.update(1000)
    assert gfx.cur_frame == 2  # stays on last frame


def test_graphics_empty_frames():
    """Test error handling for empty frame list."""
    gfx = Graphics(sprites_folder=SPRITES_DIR,
                   cell_size=(32, 32),
                   loop=True,
                   fps=10.0,
                   img_loader=MockImgFactory())

    gfx.frames = []  # explicitly empty frames list

    # No frames loaded yet
    try:
        gfx.get_img()
        assert False, "Should raise ValueError"
    except ValueError:
        pass


def test_moves_parsing_edge_cases():
    """Test Moves parser with various formats."""
    with tempfile.TemporaryDirectory() as tmp:
        moves_txt = """\
        1,0:capture
        -1,0:non_capture
        0,1:
        """

        path = pathlib.Path(tmp) / "moves.txt"
        path.write_text(moves_txt)

        mv = Moves(path, dims=(8, 8))

        # Test capture-only move
        assert mv.is_dst_cell_valid(1, 0, dst_has_piece=True)
        assert not mv.is_dst_cell_valid(1, 0, dst_has_piece=False)

        # Test non-capture-only move
        assert mv.is_dst_cell_valid(-1, 0, dst_has_piece=False)
        assert not mv.is_dst_cell_valid(-1, 0, dst_has_piece=True)

        # Test move with no tag (can both capture/non-capture)
        assert mv.is_dst_cell_valid(0, 1, dst_has_piece=True)
        assert mv.is_dst_cell_valid(0, 1, dst_has_piece=False)

        # Test invalid move coordinates
        assert not mv.is_dst_cell_valid(5, 5, dst_has_piece=True)


def test_moves_board_bounds():
    """Test that moves respect board boundaries."""
    with tempfile.TemporaryDirectory() as tmp:
        moves_txt = """\
        1,0:
        -1,0:
        0,1:
        0,-1:
        """

        path = pathlib.Path(tmp) / "moves.txt"
        path.write_text(moves_txt)

        mv = Moves(path, dims=(8, 8))

        # Test from center of board
        center = (4, 4)

        # Valid moves within bounds
        assert mv.is_valid(center, (3, 4), {})  # Up
        assert mv.is_valid(center, (5, 4), {})  # Down
        assert mv.is_valid(center, (4, 3), {})  # Left
        assert mv.is_valid(center, (4, 5), {})  # Right

        # Invalid moves beyond edges
        assert not mv.is_valid((0, 4), (-1, 4), {})  # Beyond top
        assert not mv.is_valid((7, 4), (8, 4), {})  # Beyond bottom
        assert not mv.is_valid((4, 0), (4, -1), {})  # Beyond left
        assert not mv.is_valid((4, 7), (4, 8), {})  # Beyond right
