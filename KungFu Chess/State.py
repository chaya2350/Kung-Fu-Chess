from Command import Command
from Moves import Moves
from Graphics import Graphics
from Physics import Physics
from typing import Dict
import time


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
            print(f"[TRANSITION] Arrived: {self} → {nxt}")

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
            print(f"[TRANSITION MISSING] {cmd.type} from state {self}")
            return self                      # stay put

        print(f"[TRANSITION] {cmd.type}: {self} → {nxt}")

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
