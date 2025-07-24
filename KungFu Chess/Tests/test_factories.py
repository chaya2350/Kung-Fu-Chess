import pathlib, numpy as np

from Board import Board
from img import Img
from PhysicsFactory import PhysicsFactory
from Physics import IdlePhysics, MovePhysics, JumpPhysics, RestPhysics
from PieceFactory import PieceFactory
from GraphicsFactory import GraphicsFactory, MockImgFactory

# ---------------------------------------------------------------------------
#                               HELPERS
# ---------------------------------------------------------------------------

def _blank_img(w: int = 256, h: int = 256):
    img = Img()
    img.img = np.zeros((h, w, 4), dtype=np.uint8)
    return img


def _board():
    return Board(cell_H_pix=32, cell_W_pix=32, W_cells=8, H_cells=8, img=_blank_img())

# ---------------------------------------------------------------------------
#                          PHYSICS FACTORY TESTS
# ---------------------------------------------------------------------------

def test_physics_factory_creates_correct_subclasses():
    board = _board()
    pf = PhysicsFactory(board)

    idle = pf.create((0, 0), "idle", {})
    assert isinstance(idle, IdlePhysics)

    move_cfg = {"speed_m_per_sec": 2.0}
    move = pf.create((0, 0), "move", move_cfg)
    assert isinstance(move, MovePhysics)
    assert move._speed_m_s == 2.0

    jump = pf.create((0, 0), "jump", {})
    assert isinstance(jump, JumpPhysics)

    rest_cfg = {"duration_ms": 500}
    rest = pf.create((0, 0), "long_rest", rest_cfg)
    assert isinstance(rest, RestPhysics)
    # duration stored in seconds
    assert rest.duration_s == 0.5


# ---------------------------------------------------------------------------
#                          PIECE FACTORY TESTS
# ---------------------------------------------------------------------------

def test_piece_factory_generates_and_creates_pieces():
    board = _board()
    gfx_factory = GraphicsFactory(MockImgFactory())
    p_factory = PieceFactory(board, graphics_factory=gfx_factory)

    pieces_root = pathlib.Path(__file__).parent.parent / "pieces"
    # Ensure library generation does not raise
    p_factory.generate_library(pieces_root)

    pawn = p_factory.create_piece("PW", (6, 0))
    assert pawn.id.startswith("PW_")
    assert pawn.current_cell() == (6, 0)
    assert pawn.state.name == "idle"

 
    # Create another piece type (e.g., King Black) and verify
    king = p_factory.create_piece("KB", (0, 4))
    assert king.id.startswith("KB_")
    assert king.current_cell() == (0, 4)

    # Ensure different instances (no shared state objects)
    assert king is not pawn
    assert king.state is not pawn.state 