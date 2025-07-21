import os
import pytest
import tempfile
import numpy as np
import cv2

from img import Img

# ─── fixtures ─────────────────────────────────────────────────────────────
@pytest.fixture
def tmp_image_file(tmp_path):
    # Create a simple 10×20 BGR PNG
    arr = np.zeros((10, 20, 3), dtype=np.uint8)
    arr[:] = (10, 20, 30)
    p = tmp_path / "test.png"
    assert cv2.imwrite(str(p), arr)
    return str(p)

# ─── read() tests ─────────────────────────────────────────────────────────
def test_read_file_not_found():
    img = Img()
    with pytest.raises(FileNotFoundError):
        img.read("no_such_file.png")

def test_read_without_resize(tmp_image_file):
    img = Img().read(tmp_image_file)
    assert img.img.shape == (10, 20, 3)

def test_read_resize_exact(tmp_image_file):
    img = Img().read(tmp_image_file, size=(5, 5), keep_aspect=False)
    h, w = img.img.shape[:2]
    assert (h, w) == (5, 5)

def test_read_resize_keep_aspect(tmp_image_file):
    # original 10×20, target 5×5 → scale = min(5/20,5/10)=0.25 → new = (2,5)
    img = Img().read(tmp_image_file, size=(5, 5), keep_aspect=True)
    h, w = img.img.shape[:2]
    assert (h, w) == (2, 5)

# ─── draw_on() tests ──────────────────────────────────────────────────────
def test_draw_on_value_error_when_not_loaded():
    a = Img(); b = Img()
    with pytest.raises(ValueError):
        a.draw_on(b, 0, 0)

    a.img = np.zeros((3, 3, 3), dtype=np.uint8)
    with pytest.raises(ValueError):
        a.draw_on(b, 0, 0)

    b.img = np.zeros((3, 3, 3), dtype=np.uint8)
    # now it should work
    c = Img(); c.img = np.zeros((2, 2, 3), dtype=np.uint8)
    # drawing at (1,1) fits within 3×3
    c.draw_on(b, 1, 1)
    # copying a 2×2 patch into a 3×3 image, no exception

def test_draw_on_alpha_blend():
    # background RGBA white 4×4
    bg = Img(); bg.img = np.ones((4, 4, 4), dtype=np.uint8) * 255
    # foreground RGBA red 2×2, 50% opacity
    fg = Img();
    alpha = np.full((2,2), 128, dtype=np.uint8)
    red = np.zeros((2,2,4), dtype=np.uint8)
    red[..., 2] = 255
    red[..., 3] = alpha
    fg.img = red

    fg.draw_on(bg, 1, 1)
    # at cell (1,1) the result should be halfway between white and red: (127,127,255)
    # check pixel [1,1]
    pixel = bg.img[1,1]
    assert pytest.approx(pixel[0], abs=1) == 127  # B
    assert pytest.approx(pixel[1], abs=1) == 127  # G
    assert pixel[2] == 255                        # R

# ─── put_text() tests ─────────────────────────────────────────────────────
def test_put_text_value_error_when_not_loaded():
    img = Img()
    with pytest.raises(ValueError):
        img.put_text("hi", 1, 1, 0.5)

def test_put_text_draws(tmp_image_file):
    img = Img().read(tmp_image_file)
    # must not raise
    img.put_text("OK", 1, 5, 0.4)

# ─── show() tests ─────────────────────────────────────────────────────────
def test_show_invokes_cv2(monkeypatch):
    img = Img()
    img.img = np.zeros((1,1,3), dtype=np.uint8)

    calls = {}
    def fake_imshow(win, mat):
        calls['imshow'] = (win, mat.shape)
    def fake_waitKey(x):
        calls['wait'] = x
        return 0
    def fake_destroy():
        calls['destroy'] = True

    monkeypatch.setattr(cv2, 'imshow', fake_imshow)
    monkeypatch.setattr(cv2, 'waitKey', fake_waitKey)
    monkeypatch.setattr(cv2, 'destroyAllWindows', fake_destroy)

    img.show()
    assert calls.get('imshow')[0] == "Image"
    assert calls.get('imshow')[1] == (1,1,3)
    assert calls.get('wait') == 0
    assert calls.get('destroy') is True
