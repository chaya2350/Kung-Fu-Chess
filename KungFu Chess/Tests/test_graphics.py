# test_graphics.py

import tempfile
import pathlib
import numpy as np
import pytest
from Graphics import Graphics
from img import Img
from Command import Command


@pytest.fixture
def mock_img(monkeypatch):
    """Mock Img.read to avoid actual file I/O."""
    def fake_read(self, path, size=None, keep_aspect=False, interpolation=None):
        self.img = np.ones((size[1], size[0], 4), dtype=np.uint8)
        return self
    monkeypatch.setattr(Img, "read", fake_read)


def test_load_valid_sprites(mock_img):
    with tempfile.TemporaryDirectory() as tmpdir:
        folder = pathlib.Path(tmpdir)
        (folder / "frame1.png").touch()
        (folder / "frame2.png").touch()

        g = Graphics(folder, cell_size=(64, 64), img_factory=lambda: Img())
        assert len(g.frames) == 2
        assert isinstance(g.get_img(), Img)
        assert g.get_img().img.shape == (64, 64, 4)


def test_fallback_empty_folder(monkeypatch):
    monkeypatch.setattr(Img, "__init__", lambda self, img=None: setattr(self, "img", img))
    monkeypatch.setattr(Img, "read", lambda self, *args, **kwargs: self)
    import numpy as np
    g = Graphics(pathlib.Path("."), cell_size=(10, 10), img_factory=ImgFactory(Img))

    assert isinstance(g.get_img(), Img)
    assert g.get_img().img.shape == (10, 10, 4)
    assert np.all(g.get_img().img == 0)


def test_reset_sets_timestamp(monkeypatch):
    dummy_img = Img()
    dummy_img.img = np.zeros((10, 10, 4), dtype=np.uint8)

    def dummy_loader(self, folder, size):
        return [dummy_img]

    monkeypatch.setattr("Graphics.Graphics._load_sprites", dummy_loader)

    g = Graphics(pathlib.Path("."), cell_size=(10, 10), img_factory=lambda: Img())
    cmd = Command(timestamp=1234, piece_id="P1", type="Move", params=[(1, 1)])
    g.reset(cmd)
    assert g.start_ms == 1234



def test_get_img_returns_first_frame(mock_img):
    with tempfile.TemporaryDirectory() as tmpdir:
        folder = pathlib.Path(tmpdir)
        (folder / "f.png").touch()
        g = Graphics(folder, cell_size=(32, 32), img_factory=lambda: Img())
        img = g.get_img()
        assert isinstance(img, Img)


from pathlib import Path
from img_factory import ImgFactory
from mock_img import MockImg
from Graphics import Graphics

def test_mock_graphics_loads_frames():
    sprites_folder = Path("/fake/sprites")  # can be non-existent
    gfx = Graphics(
        sprites_folder=sprites_folder,
        cell_size=(64, 64),
        img_factory=ImgFactory(MockImg)
    )
    assert len(gfx.frames) > 0 or isinstance(gfx.frames[0], MockImg)


