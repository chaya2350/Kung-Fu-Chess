import pathlib, numpy as np

from Board import Board
from Moves import Moves
from img import Img, draw_rect, close_all_img_windows


# ---------------------------------------------------------------------------
#                               BOARD & IMG
# ---------------------------------------------------------------------------


def _blank_img(w: int = 10, h: int = 10):
    img = Img()
    img.img = np.zeros((h, w, 4), dtype=np.uint8)
    return img


def test_board_cell_conversions():
    board = Board(cell_H_pix=2, cell_W_pix=2, W_cells=4, H_cells=4, img=_blank_img(8, 8))

    # Round-trip between cell ↔ metres ↔ pixels
    cell = (2, 1)
    metres = board.cell_to_m(cell)
    pix = board.m_to_pix(metres)
    back_cell = board.m_to_cell(metres)

    assert cell == back_cell
    assert pix == (1 * board.cell_W_pix, 2 * board.cell_H_pix)

    # Ensure show() and helper wrappers don’t crash head-less
    board.show()
    close_all_img_windows()



def test_img_draw_and_rectangle():
    dst = _blank_img(4, 4)
    src = _blank_img(2, 2)

    # draw small sprite centred inside dst
    src.draw_on(dst, 1, 1)

    # also exercise draw_rect helper – actual drawing is stubbed on headless env
    draw_rect(dst.img, 0, 0, 3, 3, (255, 0, 0))


# ---------------------------------------------------------------------------
#                                   MOVES
# ---------------------------------------------------------------------------


def test_moves_parsing_and_validation(tmp_path):
    moves_txt = """\
1,0:capture
-1,0:non_capture
0,1:
"""
    file_path = tmp_path / "moves.txt"
    file_path.write_text(moves_txt)

    mv = Moves(file_path, dims=(8, 8))

    # capture move allowed only if dst_has_piece
    assert mv.is_dst_cell_valid(1, 0, dst_has_piece=True)
    assert not mv.is_dst_cell_valid(1, 0, dst_has_piece=False)

    # non-capture move allowed only if destination empty
    assert mv.is_dst_cell_valid(-1, 0, dst_has_piece=False)
    assert not mv.is_dst_cell_valid(-1, 0, dst_has_piece=True)

    # move with tag "can both" (empty suffix) always allowed
    assert mv.is_dst_cell_valid(0, 1)
    assert mv.is_dst_cell_valid(0, 1, dst_has_piece=True)
