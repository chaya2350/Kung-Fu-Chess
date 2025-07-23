# Moves.py
from __future__ import annotations
import pathlib
from typing import List, Tuple

_FIRST_ONLY  =  2
_CAPTURE      = 1   # tag flag
_NON_CAPTURE  = 0
_ALWAYS       = -1  # for pieces that don't distinguish

class Moves:
    """
    Accepts three syntaxes in moves.txt  (whitespace & comments allowed)

        1  0                # old: [dr dc] or "dr,dc"
        1  0  -1            # old with explicit tag
        1,0:non_capture     # NEW
        1,-1:capture        # NEW
    """
    def __init__(self, txt_path: pathlib.Path, dims: Tuple[int, int]):
        self.rel_moves: List[Tuple[int, int, int]] = self._load_moves(txt_path)
        self.W, self.H = dims
        print(f"[LOAD] Moves from: {txt_path}")

    # ──────────────────────────────────────────────────────────────
    # public API
    def get_moves(self,
                  r: int, c: int,
                  color: str | None = None,
                  capture_only: bool = False,
                  noncap_only: bool = False,
                  allow_first: bool = False) -> list[tuple[int, int]]:
        """
        Return legal destination squares from (r,c).

        * `allow_first` lets the caller enable offsets tagged `1st`
          (e.g. the pawn’s ±2,0 double‑step) exactly when needed.
        """
        out: list[tuple[int, int]] = []
        for dr, dc, tag in self.rel_moves:
            if tag == _FIRST_ONLY and not allow_first:
                continue  # ← NEW
            if capture_only and tag != _CAPTURE:
                continue
            if noncap_only and tag == _CAPTURE:
                continue

            nr, nc = r + dr, c + dc
            if 0 <= nr < self.H and 0 <= nc < self.W:
                out.append((nr, nc))
        return out

    # ──────────────────────────────────────────────────────────────
    # internal helpers
    def _load_moves(self, fp: pathlib.Path) -> List[Tuple[int, int, int]]:
        with open(fp, encoding="utf-8") as f:
            return [self._parse(l) for l in f
                    if l.strip() and not l.lstrip().startswith("#")]

    @staticmethod
    def _parse(s: str) -> Tuple[int,int,int]:
        if ":" in s:                             # dr,dc:tag_str
            coords, tag_str = s.split(":",1)
            dr, dc = [int(x) for x in coords.split(",")]
            tag = (_CAPTURE     if tag_str=="capture" else
                   _FIRST_ONLY  if tag_str=="1st"     else
                   _NON_CAPTURE)
            return dr, dc, tag
        parts = [int(x) for x in s.replace(","," ").split()]
        if len(parts)==2:   parts.append(_ALWAYS)
        return tuple(parts)  # type:ignore
