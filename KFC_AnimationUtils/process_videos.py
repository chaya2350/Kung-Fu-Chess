#!/usr/bin/env python3
"""process_videos.py

Utility script that scans `videos/` for media files and, for each video that
does NOT already have a corresponding folder in `frames/`, runs the two helper
scripts:

1. remove_green_screen_simple.py – extracts frames while removing the green
   background.
2. frames_to_sprites.py – converts those extracted frames into cropped,
   resized sprite PNGs.

Usage:
    python process_videos.py

The script should be invoked from inside the `KFC_AnimationUtils` directory (or
anywhere within the project – it uses paths relative to this file).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Sequence


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
THIS_DIR = Path(__file__).resolve().parent
VIDEOS_DIR = THIS_DIR / "videos"
FRAMES_ROOT = THIS_DIR / "frames"
SPRITES_ROOT = THIS_DIR / "sprites"

# Video file extensions we care about
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv"}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def run(cmd: Sequence[str]) -> int:
    """Run *cmd* via subprocess and stream output. Returns the exit code."""
    print("\n$", " ".join(cmd))
    try:
        return subprocess.call(cmd)
    except KeyboardInterrupt:
        print("\nInterrupted by user. Aborting current command…", file=sys.stderr)
        return 130  # Standard interrupt exit code


def process_video(video_path: Path) -> None:
    """Process a single *video_path* through the two helper scripts."""
    base_name = video_path.stem  # file name without extension

    frames_out = FRAMES_ROOT / base_name
    sprites_out = SPRITES_ROOT / base_name

    # Skip if frames already extracted
    if frames_out.exists():
        print(f"Skipping {video_path.name} — frames already exist at '{frames_out}'.")
        return

    print("Processing", video_path.name)

    # Ensure parent directories exist
    FRAMES_ROOT.mkdir(exist_ok=True)
    SPRITES_ROOT.mkdir(exist_ok=True)

    # 1. Remove green screen / extract frames
    rc = run(
        [
            sys.executable,
            "remove_green_screen_simple.py",
            "--video",
            str(video_path),
            "--diff_thresh",
            "1",
            "--step",
            "3",
            "--out",
            str(frames_out),
        ]
    )
    if rc != 0:
        print(f"[ERROR] Green-screen removal failed for {video_path.name} (exit code {rc}). Skipping…")
        return

    # 2. Convert frames to sprites
    rc = run(
        [
            sys.executable,
            "frames_to_sprites.py",
            "--frames",
            str(frames_out),
            "--out",
            str(sprites_out),
            "--dstH",
            "128",
            "--dstW",
            "128",
        ]
    )
    if rc != 0:
        print(f"[ERROR] Sprite conversion failed for {video_path.name} (exit code {rc}).")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if not VIDEOS_DIR.is_dir():
        print(f"Videos directory not found: {VIDEOS_DIR}", file=sys.stderr)
        sys.exit(1)

    videos = sorted(p for p in VIDEOS_DIR.iterdir() if p.suffix.lower() in VIDEO_EXTS)
    if not videos:
        print("No video files found in", VIDEOS_DIR)
        return

    for video in videos:
        process_video(video)


if __name__ == "__main__":
    main() 