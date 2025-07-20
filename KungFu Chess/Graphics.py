import pathlib
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import copy
from img import Img
from Command import Command



class Graphics:
    def __init__(self,
                 sprites_folder: pathlib.Path,
                 cell_size: tuple[int, int],
                 loop: bool = True,
                 fps: float = 6.0):
        self.frames: list[Img] = self._load_sprites(sprites_folder, cell_size)
        self.loop, self.fps = loop, fps
        self.start_ms = 0
        self.cur_frame = 0
        self.frame_duration_ms = 1000 / fps
        print(f"[LOAD] Graphics from: {sprites_folder}")

    @staticmethod
    def _now_ms():
        import time
        return int(time.time() * 1000)

    def copy(self):
        # shallow copy is enough: frames list is immutable PNGs
        return copy.copy(self)

    def _load_sprites(self,
                      folder: pathlib.Path,
                      cell_size: tuple[int, int]) -> list[Img]:
        frames = []
        for p in sorted(folder.glob("*.png")):
            frames.append(Img().read(p, size=cell_size, keep_aspect=True))
        if not frames:                            # transparent 1 px fallback
            import numpy as np
            frames.append(Img(img=np.zeros((*cell_size, 4), dtype=np.uint8)))
        return frames

    def reset(self, cmd: Command):
        self.start_ms = cmd.timestamp
        self.cur_frame = 0

    def update(self, now_ms: int):
        elapsed = now_ms - self.start_ms
        frames_passed = int(elapsed / self.frame_duration_ms)
        if self.loop:
            self.cur_frame = frames_passed % len(self.frames)
        else:
            self.cur_frame = min(frames_passed, len(self.frames) - 1)

    def get_img(self) -> Img:
        if not self.frames:
            raise ValueError("No frames loaded for animation.")
        return self.frames[self.cur_frame]


