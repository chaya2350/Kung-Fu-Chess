import threading, logging
import keyboard                  # pip install keyboard
from Command import Command

logger = logging.getLogger(__name__)

class KeyboardProcessor:
    """
    Maintains a cursor on an R×C grid and maps raw key names
    into logical actions via a user‑supplied keymap.
    """
    def __init__(self, rows: int, cols: int, keymap: dict[str, str]):
        self.rows = rows
        self.cols = cols
        self.keymap = keymap
        self._cursor = [0, 0]     # [row, col]
        self._lock = threading.Lock()

    def process_key(self, event):
        # Only care about key‑down events
        if event.event_type != "down":
            return None

        key = event.name
        action = self.keymap.get(key)
        logger.debug("Key '%s' → action '%s'", key, action)

        if action in ("up", "down", "left", "right"):
            with self._lock:
                r, c = self._cursor
                if action == "up":
                    r = max(0, r - 1)
                elif action == "down":
                    r = min(self.rows - 1, r + 1)
                elif action == "left":
                    c = max(0, c - 1)
                elif action == "right":
                    c = min(self.cols - 1, c + 1)
                self._cursor = [r, c]
                logger.debug("Cursor moved to (%s,%s)", r, c)

        return action

    def get_cursor(self) -> tuple[int, int]:
        with self._lock:
            return tuple(self._cursor)


class KeyboardProducer(threading.Thread):
    """
    Runs in its own daemon thread; hooks into the `keyboard` lib,
    polls events, translates them via the KeyboardProcessor,
    and turns `select`/`jump` into Command objects on the Game queue.
    Each producer is tied to a player number (1 or 2).
    """
    def __init__(self, game, queue, processor: KeyboardProcessor, player: int):
        super().__init__(daemon=True)
        self.game = game
        self.queue = queue
        self.proc = processor
        self.player = player  # 1 or 2

    def run(self):
        # Install our hook; it stays active until we call keyboard.unhook_all()
        keyboard.hook(self._on_event)
        keyboard.wait()

    def _find_piece_at(self, cell):
        for p in self.game.pieces:
            if p.state.physics.start_cell == cell:
                return p
        return None

    def _on_event(self, event):
        action = self.proc.process_key(event)
        # only interpret select/jump
        if action in ("select", "jump"):
            cell = self.proc.get_cursor()
            # read/write the correct selected_id_X on the Game
            sel_attr = f"selected_id_{self.player}"
            selected = getattr(self.game, sel_attr)

            if selected is None:
                # first press = pick up the piece under the cursor
                #piece = self.game.pos.get(cell)
                piece = self._find_piece_at(cell)

                if piece:
                    # *optionally* only allow selection of that player's color:
                    #   if piece.id[1] == ("W" if self.player == 1 else "B"):
                    setattr(self.game, sel_attr, piece.id)
                    print(f"[KEY] Player{self.player} selected {piece.id} at {cell}")
                else:
                    print(f"[WARN] No piece at {cell}")

            else:
                # second press = issue the command
                cmd_type = "Jump" if action == "jump" else "Move"
                cmd = Command(
                    self.game.game_time_ms(),
                    selected,
                    cmd_type,
                    [cell]
                )
                self.queue.put(cmd)
                logger.info("Player%s queued %s of %s → %s at %s", self.player, cmd_type, selected, cell, cmd.timestamp)
                setattr(self.game, sel_attr, None)

    def stop(self):
        keyboard.unhook_all()
