import pathlib, tempfile, numpy as np, types
import pytest
import Graphics as gfx_mod
from img import Img

# ── helper: create a fake Img that never touches disk/CV2 ───────────────
def _mk_dummy_img():
    arr = np.zeros((10, 10, 4), dtype=np.uint8)
    obj = Img()
    obj.img = arr
    return obj

@pytest.fixture(autouse=True)
def patch_img(monkeypatch):
    """
    • Makes Img() accept any signature, incl. Img(img=array)
    • Makes Img.read(...) always succeed and set a dummy array
    """
    import numpy as np
    from img import Img                     # local import inside fixture

    # --- patch __init__ -------------------------------------------------
    def _init(self, *args, **kw):
        arr = kw.get("img") if "img" in kw else (args[0] if args else None)
        object.__setattr__(self, "img", arr)

    monkeypatch.setattr(Img, "__init__", _init, raising=True)

    # --- patch read -----------------------------------------------------
    def _read(self, *_, **__):
        self.img = np.zeros((8, 8, 4), dtype=np.uint8)     # tiny dummy RGBA
        return self

    monkeypatch.setattr(Img, "read", _read, raising=True)

    yield



# ── tests ───────────────────────────────────────────────────────────────
def test_load_valid_sprites(tmp_path):
    (tmp_path/"a.png").touch(); (tmp_path/"b.png").touch()
    g = gfx_mod.Graphics(tmp_path, (32, 32))
    assert len(g.frames) == 2

def test_fallback_empty_folder(tmp_path):
    g = gfx_mod.Graphics(tmp_path, (12, 12))
    assert g.frames and g.frames[0].img.shape[:2] == (12, 12)

def test_reset_sets_timestamp(tmp_path):
    g = gfx_mod.Graphics(tmp_path, (8, 8))
    fake_cmd = types.SimpleNamespace(timestamp=1234)
    g.reset(fake_cmd)
    assert g.start_ms == fake_cmd.timestamp


def test_get_img_returns_first_frame(tmp_path):
    (tmp_path/"foo.png").touch()
    g = gfx_mod.Graphics(tmp_path, (16, 16))
    assert g.get_img() is g.frames[0]
