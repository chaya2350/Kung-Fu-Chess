import pathlib

from Graphics import Graphics


class GraphicsFactory:
    def load(self,
             sprites_dir: pathlib.Path,
             cfg: dict,
             cell_size: tuple[int, int]) -> Graphics:
        return Graphics(
            sprites_folder=sprites_dir,
            cell_size=cell_size,                    # NEW
            loop=cfg.get("is_loop", True),
            fps=cfg.get("frames_per_sec", 6.0),
        )
