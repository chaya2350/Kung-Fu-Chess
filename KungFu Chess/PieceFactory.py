import pathlib
from typing import Dict, Tuple
import json
from Board import Board
from GraphicsFactory import GraphicsFactory
from Moves import Moves
from PhysicsFactory import PhysicsFactory
from Piece import Piece
from State import State


class PieceFactory:
    def __init__(self, board: Board):
        self.board = board
        self.physics_factory = PhysicsFactory(board)
        self.graphics_factory = GraphicsFactory()
        self.templates: Dict[str, State] = {}

    # Scan folders once, cache ready-made state machines -----------
    def generate_library(self, pieces_root: pathlib.Path):
        for sub in pieces_root.iterdir():
            # “…/PW” etc.
            self.templates[sub.name] = self._build_state_machine(sub)

    def _build_state_machine(self, piece_dir: pathlib.Path) -> State:
        board_size = (self.board.W_cells, self.board.H_cells)
        cell_px = (self.board.cell_W_pix, self.board.cell_H_pix)

        states: Dict[str, State] = {}

        # ── scan every sub-folder inside “states” ────────────────────────────
        for state_dir in (piece_dir / "states").iterdir():
            if not state_dir.is_dir():  # skip stray files
                continue

            name = state_dir.name  # idle / move / jump / …

            # 1. config --------------------------------------------------------
            cfg_path = state_dir / "config.json"

            if cfg_path.exists() and cfg_path.read_text().strip():
                cfg = json.loads(cfg_path.read_text())
            else:
                cfg = {}

            # 2. moves ---------------------------------------------------------
            moves = Moves(state_dir / "moves.txt", board_size)


            # 3. graphics & physics -------------------------------------------
            graphics = self.graphics_factory.load(state_dir / "sprites",
                                                  cfg["graphics"], cell_px)
            physics = self.physics_factory.create((0, 0), cfg["physics"])

            state = State(moves, graphics, physics)
            state.name = name
            states[name] = state

        # ── wire transitions  (Arrived → next_state_when_finished) ───────────
        for name, st in states.items():
            # Read per-state config again
            cfg_path = piece_dir / "states" / name / "config.json"
            cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}

            nxt_name = cfg.get("physics", {}).get("next_state_when_finished")
            if nxt_name and nxt_name in states:
                st.set_transition("Arrived", states[nxt_name])

        # ── default external transitions -------------------------------------
        for st in states.values():
            if "move" in states:
                st.set_transition("Move", states["move"])
            if "jump" in states:
                st.set_transition("Jump", states["jump"])

        return states.get("idle") or next(iter(states.values()))

    # PieceFactory.py  – replace create_piece(...)
    # PieceFactory.py  – revised create_piece()
    def create_piece(self, p_type: str, cell: Tuple[int, int]) -> Piece:
        template_idle = self.templates[p_type]

        # create ONE physics object at the real start cell
        shared_phys = self.physics_factory.create(cell, {})

        clone_map: Dict[State, State] = {}
        stack = [template_idle]
        while stack:
            orig = stack.pop()
            if orig in clone_map:
                continue

            clone_map[orig] = State(
                moves=orig.moves,  # safe to share
                graphics=orig.graphics.copy(),  # each piece gets its own gfx
                physics=shared_phys  # ← SAME physics for all states
            )
            clone_map[orig].name = orig.name
            stack.extend(orig.transitions.values())

        # re-wire transitions
        for orig, clone in clone_map.items():
            for ev, target in orig.transitions.items():
                clone.set_transition(ev, clone_map[target])

        return Piece(f"{p_type}_{cell}", clone_map[template_idle])


