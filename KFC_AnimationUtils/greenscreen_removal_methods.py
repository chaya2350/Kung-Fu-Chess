import cv2
import numpy as np

# ──────────────────────────────────────────────────────────────────────
#  Simple chroma-key removal (moved from remove_green_screen_simple.py)
# ──────────────────────────────────────────────────────────────────────

GREEN_KERNEL = np.ones((3, 3), np.uint8)

def greenscreen_remove_simple(frame_bgr: np.ndarray) -> np.ndarray:
    """Return an RGBA image with green pixels made fully transparent.

    This is the original heuristic method that considers a pixel background
    if the green channel is considerably stronger than the red & blue
    channels.
    """
    B, G, R = [c.astype(np.float32) for c in cv2.split(frame_bgr)]
    green_thresh = np.minimum(R + 0.5 * B, 0.5 * R + B)
    mask = (G > green_thresh).astype(np.uint8)
    mask = cv2.dilate(mask, GREEN_KERNEL, iterations=1)
    alpha = np.where(mask > 0, 0, 255).astype(np.uint8)

    rgba = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = alpha
    return rgba

# ──────────────────────────────────────────────────────────────────────
#  Segmentation-based removal using GrabCut
# ──────────────────────────────────────────────────────────────────────

def greenscreen_remove_segmentation(frame_bgr: np.ndarray) -> np.ndarray:
    """Remove green background using GrabCut segmentation.

    Workflow:
    1. Pixels where G > max(R, B) + margin are marked as likely background.
    2. These pixels plus a small image border are provided to GrabCut as
       *sure background*, everything else as *probable foreground*.
    3. GrabCut refines the mask to separate the main object from the green
       background.
    4. The resulting mask is converted to an RGBA image with transparency.
    """
    h, w, _ = frame_bgr.shape

    # Step 1: obvious green background
    B, G, R = cv2.split(frame_bgr)
    margin = 5  # small tolerance so that near-neutral pixels stay untouched
    initial_bg = (G.astype(np.int16) > np.maximum(R, B) + margin).astype(np.uint8)

    # Step 2: erode to shrink background mask and avoid halos
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    initial_bg = cv2.erode(initial_bg, kernel, iterations=1)

    # Prepare the GrabCut mask – non-green area is *probable foreground*
    grabcut_mask = np.full((h, w), cv2.GC_PR_FGD, dtype=np.uint8)  # probable FG by default
    grabcut_mask[initial_bg == 1] = cv2.GC_BGD                     # sure background

    # Border of the frame is almost certainly background — mark as sure bg
    border = 5
    grabcut_mask[:border, :] = cv2.GC_BGD
    grabcut_mask[-border:, :] = cv2.GC_BGD
    grabcut_mask[:, :border] = cv2.GC_BGD
    grabcut_mask[:, -border:] = cv2.GC_BGD

    # Step 4: GrabCut refinement
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    cv2.grabCut(frame_bgr, grabcut_mask, None, bgd_model, fgd_model,
                5, mode=cv2.GC_INIT_WITH_MASK)

    mask_fg = np.where((grabcut_mask == cv2.GC_FGD) | (grabcut_mask == cv2.GC_PR_FGD),
                       1, 0).astype(np.uint8)
    mask_fg = cv2.morphologyEx(mask_fg, cv2.MORPH_CLOSE, kernel, iterations=2)

    alpha = (mask_fg * 255).astype(np.uint8)
    rgba = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = alpha
    return rgba

# ──────────────────────────────────────────────────────────────────────
#  Background-subtractor-based removal (for video sequences)
# ──────────────────────────────────────────────────────────────────────

def _lazy_subtractor():
    """Create (once) and return a high-quality background subtractor."""
    if not hasattr(_lazy_subtractor, "sub"):
        _lazy_subtractor.sub = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=16, detectShadows=False)
    return _lazy_subtractor.sub

def greenscreen_remove_bg_subtractor(frame_bgr: np.ndarray) -> np.ndarray:
    """Remove background using an adaptive background subtractor (MOG2).

    Best suited when called on *consecutive* frames from the same video so
    that the background model can learn the static scene.
    """
    subtractor = _lazy_subtractor()
    fg_mask = subtractor.apply(frame_bgr)

    # Clean up the mask
    _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel, iterations=2)

    rgba = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = fg_mask.astype(np.uint8)
    return rgba

# ──────────────────────────────────────────────────────────────────────
#  Public registry helpers
# ──────────────────────────────────────────────────────────────────────

METHODS = {
    "simple": greenscreen_remove_simple,
    "segment": greenscreen_remove_segmentation,
    "bgsub": greenscreen_remove_bg_subtractor,
}

def get_method(name: str):
    """Return a removal function by name (case-sensitive)."""
    try:
        return METHODS[name]
    except KeyError as e:
        raise ValueError(f"Unknown removal method '{name}'. Valid options: {list(METHODS.keys())}") from e 