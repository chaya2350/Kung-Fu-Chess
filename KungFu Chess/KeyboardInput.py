import threading, queue
from typing import Tuple, Optional

import keyboard  # external dependency: pip install keyboard

from Command import Command


class KeyboardProcessor:
    """Maintain cursor location and selection state based on key presses."""

    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols

        # board-relative coordinates (row, col)
        self.cursor: Tuple[int, int] = (rows // 2, cols // 2)

        # two-step selection: first pick a piece, then pick destination square
        self._stage: str = "select"  # or "dest"
        self._selected_piece_id: Optional[str] = None

        # re-entrant safety – Game + Producer can query state concurrently
        self._lock = threading.Lock()

    # ────────────────────────────────────────────────────────────────────
    def _clamp(self, v: int, lo: int, hi: int) -> int:
        return max(lo, min(hi, v))

    def move_cursor(self, dr: int, dc: int):
        """Move cursor by (dr, dc) within board bounds."""
        with self._lock:
            r, c = self.cursor
            r = self._clamp(r + dr, 0, self.rows - 1)
            c = self._clamp(c + dc, 0, self.cols - 1)
            self.cursor = (r, c)

    # ────────────────────────────────────────────────────────────────────
    def process_key(self, key_name: str, game) -> Optional[Command]:
        """Handle an OS key *down* event. Return a Command if one is produced."""
        MOVE_VECTORS = {
            "up": (-1, 0),
            "down": (1, 0),
            "left": (0, -1),
            "right": (0, 1),
        }

        if key_name in MOVE_VECTORS:
            dr, dc = MOVE_VECTORS[key_name]
            self.move_cursor(dr, dc)
            return None  # just moved cursor

        if key_name == "enter":
            return self._handle_enter(game)

        return None

    # ────────────────────────────────────────────────────────────────────
    def _handle_enter(self, game) -> Optional[Command]:
        """ENTER either selects a piece or finalises a move."""
        with self._lock:
            cell = self.cursor
            if self._stage == "select":
                piece = game.pos.get(cell)
                if piece is not None:
                    self._selected_piece_id = piece.id
                    self._stage = "dest"  # next ENTER will be destination
            else:  # stage == dest
                if self._selected_piece_id is None:
                    # Somehow lost the piece reference – reset.
                    self._stage = "select"
                    return None

                cmd = Command(
                    game.game_time_ms(),
                    self._selected_piece_id,
                    "Move",  # keyboard interface only supports normal Move
                    [cell],
                )
                # reset state for next move
                self._stage = "select"
                self._selected_piece_id = None
                return cmd
        return None

    # ────────────────────────────────────────────────────────────────────
    def get_cursor(self) -> Tuple[int, int]:
        with self._lock:
            return self.cursor


class KeyboardProducer(threading.Thread):
    """Background thread feeding Commands to Game.user_input_queue."""

    def __init__(self, game, output_queue: "queue.Queue[Command]", processor: KeyboardProcessor):
        super().__init__(daemon=True)
        self._game = game
        self._output_queue = output_queue
        self._proc = processor
        self._running = threading.Event()
        self._running.set()

    # ────────────────────────────────────────────────────────────────────
    def run(self):
        while self._running.is_set():
            event = keyboard.read_event()
            if event.event_type != keyboard.KEY_DOWN:
                continue  # ignore KEY_UP

            key = event.name  # e.g. "up", "a", "enter"
            if key == "esc":
                # allow player to quit via ESC
                self.stop()
                break

            cmd = self._proc.process_key(key, self._game)
            if cmd is not None:
                self._output_queue.put(cmd)

    # ────────────────────────────────────────────────────────────────────
    def stop(self):
        self._running.clear() 