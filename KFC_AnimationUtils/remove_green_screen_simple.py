import cv2
import numpy as np
from pathlib import Path
import argparse
from greenscreen_removal_methods import get_method, METHODS

GREEN_KERNEL = np.ones((3, 3), np.uint8)

def greenscreen_remove(frame_bgr: np.ndarray) -> np.ndarray:
    """Return an RGBA image with green pixels made fully transparent."""
    B, G, R = [c.astype(np.float32) for c in cv2.split(frame_bgr)]
    green_thresh = np.minimum(R + 0.5 * B, 0.5 * R + B)
    mask = (G > green_thresh).astype(np.uint8)
    mask = cv2.dilate(mask, GREEN_KERNEL, iterations=1)
    alpha = np.where(mask > 0, 0, 255).astype(np.uint8)

    rgba = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = alpha
    return rgba

def process_video(video_path: str,
                  output_dir: str,
                  method: str = "simple",
                  start_sec: float = 0.0,
                  diff_thresh: float = 2.0,
                  invert: bool = False,
                  step: int = 1):

    if step < 1:
        raise ValueError("--step must be ≥ 1")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30  # use 30 fps fallback if 0
    start_frame = int(round(start_sec * fps))
    if start_frame:
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    # Select the requested greenscreen-removal function once per video
    removal_fn = get_method(method)

    # reference frame = first frame after any skip
    ret, ref_frame = cap.read()
    if not ret:
        raise RuntimeError(f"Failed to read frame at t={start_sec}s")

    Path(output_dir).mkdir(exist_ok=True)
    out_idx = 1  # numbering of written files
    frame_idx = 1  # count of processed frames (for step logic)

    def maybe_save(img_bgr):
        nonlocal out_idx
        img_rgba = removal_fn(img_bgr)
        if invert:
            img_rgba[:, :, :3] = 255 - img_rgba[:, :, :3]
        cv2.imwrite(f"{output_dir}/{out_idx}.png", img_rgba)
        out_idx += 1

    # save reference frame (always)
    maybe_save(ref_frame)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Reached end‑of‑file.")
            break

        # early‑stop test (compare every frame, even if not saved)
        if cv2.absdiff(frame, ref_frame).mean() <= diff_thresh and diff_thresh > 30:
            print(f"Stopping: current frame similar to first (≤ {diff_thresh}).")
            break

        # save only every K‑th frame
        frame_idx += 1
        if (frame_idx - 1) % step == 0:         # (frame 2 is idx 1, etc.)
            maybe_save(frame)

        if out_idx % 50 == 0:
            print(f"Saved {out_idx} frames...")

    cap.release()
    print(f"Done! Saved {out_idx-1} frames to '{output_dir}'")

# ────────────────────────────── CLI ──────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Greenscreen remover")
    ap.add_argument("--video", required=True, help="Input video file")
    ap.add_argument("--out",   required=True, help="Output directory")
    ap.add_argument("--start_sec",  type=float, default=0.0,
                    help="Skip this many seconds before processing")
    ap.add_argument("--diff_thresh", type=float, default=2.0,
                    help="Stop when mean abs diff with first frame ≤ this")
    ap.add_argument("--invert", action="store_true",
                    help="Invert colours of saved frames")
    ap.add_argument("--step", type=int, default=1,
                    help="Save only every K-th frame (default 1 = all)")
    ap.add_argument("--method", choices=list(METHODS.keys()), default="simple",
                    help="Greenscreen removal algorithm to use")
    args = ap.parse_args()

    process_video(args.video, args.out,
                  method=args.method,
                  start_sec=args.start_sec,
                  diff_thresh=args.diff_thresh,
                  invert=args.invert,
                  step=args.step)

# # Basic usage
# python gs.py --video clip.mp4 --out frames/

# # Skip first 2 s, save every 3rd frame, colours inverted
# python gs.py --video clip.mp4 --out frames_inv/ \
#              --start_sec 2 --step 3 --invert
