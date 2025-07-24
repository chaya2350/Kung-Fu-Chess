import pathlib, pytest

# NOTE: These tests reflect the *desired* public API the production code
# will soon provide.  They are expected to FAIL until the implementation
# is completed.

from mock_img import MockImg

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT_DIR = pathlib.Path(__file__).parent.parent
PIECES_DIR = ROOT_DIR / "pieces"

# ---------------------------------------------------------------------------
# create_game helper expected from GameFactory
# ---------------------------------------------------------------------------

def test_create_game_builds_full_board():
    """create_game() should return a fully-initialised *Game* with 32 pieces."""
    from GameFactory import create_game  # noqa: F401 – will fail if not implemented

    game = create_game(PIECES_DIR)

    from Game import Game
    assert isinstance(game, Game)
    assert len(game.pieces) == 32  # standard chess starting position


# ---------------------------------------------------------------------------
# GraphicsFactory should accept an *img_factory* injectable for head-less tests
# ---------------------------------------------------------------------------

def test_graphics_factory_uses_custom_img_factory():
    """GraphicsFactory(img_factory=…) should forward loader to Graphics objects."""
    from GraphicsFactory import GraphicsFactory  # noqa: F401 – expected future interface

    # Simple callable that returns a *MockImg* regardless of path
    def _mock_loader(path, cell_size, keep_aspect=False):  # noqa: D401
        img = MockImg()
        img.read(path, cell_size, keep_aspect=keep_aspect)
        return img

    gf = GraphicsFactory(img_factory=_mock_loader)  # type: ignore[arg-type]

    sprites_dir = PIECES_DIR / "PW" / "states" / "idle" / "sprites"
    gfx = gf.load(sprites_dir, cfg={}, cell_size=(32, 32))  # noqa: F841 – future Graphics

    # After load, every frame in *gfx* should be a *MockImg*
    for frm in gfx.frames:  # type: ignore[attr-defined]
        assert isinstance(frm, MockImg) 