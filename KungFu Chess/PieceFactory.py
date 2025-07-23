# PieceFactory.py
from __future__ import annotations
import csv, json, pathlib
from typing import Dict, Tuple

from Board           import Board
from GraphicsFactory import GraphicsFactory
from Moves           import Moves
from PhysicsFactory  import PhysicsFactory
from Piece           import Piece
from State           import State


class PieceFactory:
    def __init__(self,
                 board: Board,
                 graphics_factory=None,
                 physics_factory=None):
        self.board            = board
        self.graphics_factory = graphics_factory or GraphicsFactory()
        self.physics_factory  = physics_factory or PhysicsFactory(board)
        self.templates: Dict[str, State] = {}
        self._global_trans: dict[str, dict[str, str]] = {}

    # ──────────────────────────────────────────────────────────────
    def _load_master_csv(self, pieces_root: pathlib.Path) -> None:
        if self._global_trans:                     # already read
            return
        csv_path = pieces_root.parent / "state_transitions.csv"
        if not csv_path.exists():
            print("[WARN] state_transitions.csv not found; using defaults")
            return
        with csv_path.open(newline="", encoding="utf-8") as f:
            rdr = csv.DictReader(f)
            for row in rdr:                        # from_state,event,to_state
                frm, ev, nxt = row["from_state"], row["event"], row["to_state"]
                self._global_trans.setdefault(frm, {})[ev] = nxt
        print(f"[LOAD] global transitions from {csv_path}")

    # ──────────────────────────────────────────────────────────────
    def generate_library(self, pieces_root: pathlib.Path) -> None:
        self._load_master_csv(pieces_root)
        for sub in pieces_root.iterdir():          # “PW”, “KN”, …
            if sub.is_dir():
                self.templates[sub.name] = self._build_state_machine(sub)

    # ──────────────────────────────────────────────────────────────
    def _build_state_machine(self, piece_dir: pathlib.Path) -> State:
        board_size = (self.board.W_cells, self.board.H_cells)
        cell_px    = (self.board.cell_W_pix, self.board.cell_H_pix)

        states: Dict[str, State] = {}

        # optional piece‑wide moves.txt
        common_moves = None
        cm_path = piece_dir / "moves.txt"
        if cm_path.exists():
            common_moves = Moves(cm_path, board_size)

        # ── load every <piece>/states/<state>/ ───────────────────
        for state_dir in (piece_dir / "states").iterdir():
            if not state_dir.is_dir():
                continue
            name = state_dir.name

            cfg_path = state_dir / "config.json"
            cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}

            moves    = common_moves or Moves(state_dir / "moves.txt", board_size)
            graphics = self.graphics_factory.load(state_dir / "sprites",
                                                  cfg.get("graphics", {}), cell_px)
            physics  = self.physics_factory.create((0, 0), cfg.get("physics", {}))

            st = State(moves, graphics, physics)
            st.name = name
            states[name] = st

        # default external transitions
        for st in states.values():
            if "move" in states: st.set_transition("Move",  states["move"])
            if "jump" in states: st.set_transition("Jump",  states["jump"])

        # apply master CSV overrides
        for frm, ev_map in self._global_trans.items():
            src = states.get(frm)
            if not src:
                continue
            for ev, nxt in ev_map.items():
                dst = states.get(nxt)
                if dst:
                    src.set_transition(ev, dst)

        # pawn: add first‑move chain
        if piece_dir.name.startswith("P"):
            self._pawn_first_move(states)

        # pawn starts in first_idle, others in idle
        return (states.get("first_idle")
                or states.get("idle")
                or next(iter(states.values())))

    # ──────────────────────────────────────────────────────────────
    def _pawn_first_move(self, states: Dict[str, State]) -> None:
        """
        Inject two transient states so a pawn can do the one‑time double step.

            first_idle --Move--> first_move --Arrived--> idle
        """
        if "first_idle" in states or "idle" not in states or "move" not in states:
            return

        idle = states["idle"]
        move = states["move"]

        # clone idle → first_idle
        first_idle = State(idle.moves, idle.graphics.copy(), idle.physics)
        first_idle.name = "first_idle"
        states["first_idle"] = first_idle

        # clone move → first_move
        first_move = State(move.moves, move.graphics.copy(), move.physics)
        first_move.name = "first_move"
        states["first_move"] = first_move

        # wiring
        first_idle.set_transition("Move", first_move)  # first move can use ±2
        first_move.set_transition("Arrived", idle)  # ALWAYS drop to idle

        print(first_move.name)

    # ──────────────────────────────────────────────────────────────
    def create_piece(self, p_type: str, cell: Tuple[int, int]) -> Piece:
        template_idle = self.templates[p_type]

        # share ONE physics object per piece instance
        shared_phys = self.physics_factory.create(cell, {})

        clone_map: Dict[State, State] = {}
        stack = [template_idle]
        while stack:
            orig = stack.pop()
            if orig in clone_map:
                continue
            clone = State(orig.moves,
                          orig.graphics.copy(),
                          shared_phys)
            clone.name = orig.name
            clone_map[orig] = clone
            stack.extend(orig.transitions.values())

        # re‑wire transitions
        for orig, clone in clone_map.items():
            for ev, target in orig.transitions.items():
                clone.set_transition(ev, clone_map[target])

        return Piece(f"{p_type}_{cell}", clone_map[template_idle])
