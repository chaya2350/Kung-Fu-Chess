#!/usr/bin/env python3
"""frames_to_sprites.py

Utility that converts a folder of RGBA video-frame images into cropped
sprites of fixed size.

Steps:
1. For every frame in the input folder, compute the bounding rectangle of
   the visible (alpha>0) pixels.
2. Take the union of all per-frame rectangles, then expand this rectangle
   by 10 % on every side.
3. Crop *every* frame to this final rectangle.
4. Resize the crop to --dstH × --dstW and save it into the output folder.

Example
-------
python frames_to_sprites.py --frames frames/ \
                           --out sprites/ \
                           --dstH 64 --dstW 64
"""
from __future__ import annotations

import cv2
import numpy as np
from pathlib import Path
import argparse
from typing import Tuple, List

# ---------------------------------------------------------------------------
#                               CORE LOGIC
# ---------------------------------------------------------------------------

def _frame_rect(img: np.ndarray) -> Tuple[int, int, int, int] | None:
    """Return bounding rectangle (x1, y1, x2, y2) of non-transparent pixels.
    If the image has no visible pixels, return None.
    Assumes `img` is BGRA with alpha in channel 3.
    """
    if img.shape[2] < 4:
        raise ValueError("Input images must have an alpha channel (BGRA)")
    alpha = img[:, :, 3]
    ys, xs = np.nonzero(alpha > 0)
    if len(xs) == 0:
        return None  # fully transparent
    x1, x2 = int(xs.min()), int(xs.max())
    y1, y2 = int(ys.min()), int(ys.max())
    return x1, y1, x2, y2

def _union_rect(rects: List[Tuple[int, int, int, int]]) -> Tuple[int, int, int, int]:
    """Return minimal rectangle that contains all rectangles in *rects*."""
    x1 = min(r[0] for r in rects)
    y1 = min(r[1] for r in rects)
    x2 = max(r[2] for r in rects)
    y2 = max(r[3] for r in rects)
    return x1, y1, x2, y2


def _expand_rect(rect: Tuple[int, int, int, int], w_max: int, h_max: int, margin_ratio: float = 0.10) -> Tuple[int, int, int, int]:
    """Expand *rect* by *margin_ratio* of its width/height on every side.
    Clamp to the image bounds given by *w_max*, *h_max*.
    """
    x1, y1, x2, y2 = rect
    width = x2 - x1 + 1
    height = y2 - y1 + 1
    dx = int(round(width * margin_ratio))
    dy = int(round(height * margin_ratio))
    new_x1 = max(0, x1 - dx)
    new_y1 = max(0, y1 - dy)
    new_x2 = min(w_max - 1, x2 + dx)
    new_y2 = min(h_max - 1, y2 + dy)
    return new_x1, new_y1, new_x2, new_y2

# ---------------------------------------------------------------------------
#                               PIPELINE
# ---------------------------------------------------------------------------


def process_frames(frames_dir: Path, out_dir: Path, dst_h: int, dst_w: int):
    if not frames_dir.is_dir():
        raise FileNotFoundError(f"Input directory not found: {frames_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    frame_paths = sorted([p for p in frames_dir.iterdir() if p.suffix.lower() in {".png", ".tif", ".tiff", ".bmp"}])
    if not frame_paths:
        raise RuntimeError("No image frames found in input directory.")

    # Pass 1: determine union bounding rectangle
    rects = []
    w_max = h_max = None
    for fp in frame_paths:
        img = cv2.imread(str(fp), cv2.IMREAD_UNCHANGED)
        if img is None:
            print(f"Warning: failed to read {fp}, skipping.")
            continue
        if img.shape[2] < 4:
            print(f"Warning: {fp} lacks alpha channel, skipping.")
            continue
        if w_max is None:
            h_max, w_max = img.shape[:2]
        rect = _frame_rect(img)
        if rect:
            rects.append(rect)
    if not rects:
        raise RuntimeError("All frames are fully transparent; nothing to crop.")

    union = _union_rect(rects)
    final_rect = _expand_rect(union, w_max, h_max)

    # Pass 2: crop, resize, save
    for fp in frame_paths:
        img = cv2.imread(str(fp), cv2.IMREAD_UNCHANGED)
        if img is None or img.shape[2] < 4:
            continue  # already warned earlier
        x1, y1, x2, y2 = final_rect
        crop = img[y1:y2+1, x1:x2+1].copy()
        sprite = cv2.resize(crop, (dst_w, dst_h), interpolation=cv2.INTER_AREA)
        out_fp = out_dir / fp.name
        cv2.imwrite(str(out_fp), sprite)
    print(f"Processed {len(frame_paths)} frames → {out_dir}")

# ---------------------------------------------------------------------------
#                               CLI ENTRY
# ---------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description="Convert RGBA video frames to cropped & resized sprites.")
    ap.add_argument("--frames", required=True, help="Input directory containing RGBA frames")
    ap.add_argument("--out", required=True, help="Output directory for sprites")
    ap.add_argument("--dstH", type=int, required=True, help="Destination sprite height")
    ap.add_argument("--dstW", type=int, required=True, help="Destination sprite width")
    args = ap.parse_args()

    process_frames(Path(args.frames), Path(args.out), args.dstH, args.dstW)


if __name__ == "__main__":
    main() 