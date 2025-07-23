from __future__ import annotations
from Command import Command
from Moves import Moves
from Graphics import Graphics
from Physics import Physics
from typing import Dict, Callable
import time, logging

from Piece import Piece

logger = logging.getLogger(__name__)


class State:
    def __init__(self, moves: Moves, graphics: Graphics, physics: Physics):
        self.moves, self.graphics, self.physics = moves, graphics, physics
        self.transitions: Dict[str, "State"] = {}
        self.cooldown_end_ms = 0
        self.name = None

    def __repr__(self):
        return f"State({self.name})"

        # configuration ------------
    def set_transition(self, event: str, target: "State"):
        self.transitions[event] = target

    # runtime -------------------
    def reset(self, cmd: Command):
        self.graphics.reset(cmd)
        self.physics.reset(cmd)
        #
        # if cmd.type == "Move":
        #     self.cooldown_end_ms = cmd.timestamp + 6_000      # 6 s
        # elif cmd.type == "Jump":
        #     self.cooldown_end_ms = cmd.timestamp + 3_000      # 3 s


    def can_transition(self, now_ms: int) -> bool:           # customise per state
        return now_ms >= self.cooldown_end_ms

    def get_state_after_command(self, cmd: Command, now_ms: int) -> "State":
        nxt = self.transitions.get(cmd.type)

        # ── internal transition fired by Physics.update() ─────────────────
        if cmd.type == "Arrived" and nxt:
            logger.debug("[TRANSITION] Arrived: %s → %s", self, nxt)

            # 1️⃣ choose rest length according to the *previous* action
            if self.name == "move":
                rest_ms = 6000  # long rest after Move
            elif self.name == "jump":
                rest_ms = 3000  # short rest after Jump
            else:  # long_rest → idle, idle → idle, …
                rest_ms = 0

            # 2️⃣ restart graphics of the next state
            nxt.graphics.reset(cmd)

            # 3️⃣ arm the Physics timer *only if* we have to wait
            if rest_ms:
                p = nxt.physics
                p.start_ms = now_ms  # timer starts *now*
                p.duration_ms = rest_ms
                p.wait_only = True

                nxt.cooldown_end_ms = now_ms + rest_ms
            else:
                nxt.cooldown_end_ms = 0

            return nxt

        if nxt is None:
            logger.warning("[TRANSITION_MISSING] %s from state %s", cmd.type, self)
            return self                      # stay put

        logger.debug("[TRANSITION] %s: %s → %s", cmd.type, self, nxt)

        # if cooldown expired, perform the transition
        if self.can_transition(now_ms):
            nxt.reset(cmd)                   # this starts the travel
            return nxt

        # cooldown not finished → refresh current physics/graphics
        self.reset(cmd)
        return self


    def update(self, now_ms: int) -> "State":
        internal = self.physics.update(now_ms)
        if internal:
            print("[DBG] internal:", internal.type)
            return self.get_state_after_command(internal, now_ms)
        self.graphics.update(now_ms)
        return self

    def get_command(self) -> Command:
        # Minimal placeholder – extend as needed.
        return Command(self.physics.start_ms, "?", "Idle", [])

    def is_legal(self,
                 mover: Piece,
                 cmd: Command,
                 pos: dict[tuple[int, int], Piece],
                 path_is_clear: Callable[[tuple[int, int], tuple[int, int]], bool]
                 ) -> bool:
        src, dest = mover.current_cell(), cmd.params[0]
        #TODO: current cell not relevant on move
        piece_type, color = mover.id[0], mover.id[1]

        # ignore self‑occupancy so jumping to your own square isn’t "friendly"
        occ = pos.get(dest)
        if occ is mover:
            occ = None
        friendly = (occ is not None and occ.id[1] == color)

        # 1) compute basic legality
        #TODO: @stoped here
        if piece_type == "P" and cmd.type != "Jump":
            # ––––– determine occupancy once –––––
            occ = pos.get(dest)

            allow_first = mover.state.name.startswith("first_idle")

            legal = dest in self.moves.get_moves(*src,
                                                 color,
                                                 capture_only=(occ is not None),
                                                 noncap_only=(occ is None),
                                                 allow_first=allow_first)
        else:
            # all other pieces: either in your Moves set or a Jump command
            legal = (cmd.type == "Jump" or dest in self.moves.get_moves(*src))



        # 2) path clearance: skip for Jump or knights
        if cmd.type == "Jump" or piece_type == "N":
            clear = True
        elif piece_type in ("R", "B", "Q", "P"):
            clear = path_is_clear(src, dest)
        else:
            clear = True

        print(f"Is legal: {legal}, Is clear: {clear}, Is friendly: {friendly}")
        return legal and clear and not friendly
