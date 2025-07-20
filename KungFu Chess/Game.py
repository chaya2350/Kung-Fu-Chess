import queue, threading, time, cv2, math
from typing import List, Dict, Tuple, Optional

from Board   import Board
from Command import Command
from Piece   import Piece
from img     import Img


class InvalidBoard(Exception): ...
# ────────────────────────────────────────────────────────────────────
class Game:
    def __init__(self, pieces: List[Piece], board: Board):
        if not self._validate(pieces):
            raise InvalidBoard("duplicate pieces or no king")
        self.pieces           = pieces
        self.board            = board
        self.START_NS         = time.monotonic_ns()
        self.user_input_queue = queue.Queue()          # thread-safe
        self.selected_id: Optional[str] = None         # piece currently picked

        # fast lookup tables ---------------------------------------------------
        self.pos            : Dict[Tuple[int, int], Piece] = {}
        self.piece_by_id    : Dict[str, Piece] = {p.id: p for p in pieces}

    # ─── helpers ─────────────────────────────────────────────────────────────
    def game_time_ms(self) -> int:
        return (time.monotonic_ns() - self.START_NS) // 1_000_000

    def clone_board(self) -> Board:
        """
        Return a **brand-new** Board wrapping a copy of the background pixels
        so we can paint sprites without touching the pristine board.
        """
        img_copy = Img()
        img_copy.img = self.board.img.img.copy()
        return Board(self.board.cell_H_pix, self.board.cell_W_pix,
                     self.board.W_cells,    self.board.H_cells,
                     img_copy)

    # ─── input thread – mouse → Command objects ─────────────────────────────
    # Game._mouse_cb – add a check for right button
    def _mouse_cb(self, event, x, y, flags, userdata):
        event_is_down = event in (cv2.EVENT_LBUTTONDOWN, cv2.EVENT_RBUTTONDOWN)
        if not event_is_down:
            return

        is_jump = (event == cv2.EVENT_RBUTTONDOWN)

        cell = (y // self.board.cell_H_pix, x // self.board.cell_W_pix)

        if self.selected_id is None:  # 1st click: select
            piece = self.pos.get(cell)
            if piece:
                self.selected_id = piece.id
        else:
            cmd_type = "Jump" if is_jump else "Move"
            cmd = Command(self.game_time_ms(),
                          self.selected_id,
                          cmd_type,
                          [cell])
            self.user_input_queue.put(cmd)
            self.selected_id = None

    def start_user_input_thread(self):
        # OpenCV’s mouse callbacks run in the main thread, so we just register it
        cv2.namedWindow("Kung-Fu Chess")
        cv2.setMouseCallback("Kung-Fu Chess", self._mouse_cb)

    # ─── main public entrypoint ──────────────────────────────────────────────
    def run(self):
        self.start_user_input_thread()
        start_ms = self.game_time_ms()
        for p in self.pieces:
            p.reset(start_ms)

        # ─────── main loop ──────────────────────────────────────────────────
        while not self._is_win():
            now = self.game_time_ms()

            # (1) update physics & animations
            for p in self.pieces:
                p.update(now)

            # (2) handle queued Commands from mouse thread
            while not self.user_input_queue.empty():
                cmd: Command = self.user_input_queue.get()
                self._process_input(cmd)

            # (3) draw current position
            self._draw()
            if not self._show():           # returns False if user closed window
                break

            # (4) detect captures
            self._resolve_collisions()

        self._announce_win()
        cv2.destroyAllWindows()

    # ─── drawing helpers ────────────────────────────────────────────────────
    def _draw(self):
        self.curr_board = self.clone_board()
        # rebuild position map each frame
        self.pos.clear()
        for p in self.pieces:
            p.draw_on_board(self.curr_board, now_ms=self.game_time_ms())
            self.pos[p.state.physics.start_cell] = p

    def _show(self) -> bool:
        cv2.imshow("Kung-Fu Chess", self.curr_board.img.img)
        key = cv2.waitKey(1) & 0xFF
        return key != 27  # only Esc quits

    def _side_of(self, piece_id: str) -> str:
        """
        Return 'W' or 'B' from an id formatted like 'PW_(6,1)'.
        Second character after the initial type letter is the colour.
        """
        return piece_id[1]  # e.g. 'PW' → 'W'  ·  'KB' → 'B'

    def _path_is_clear(self, a, b):
        ar, ac = a
        br, bc = b
        dr = (br - ar) and ((br - ar) // abs(br - ar))
        dc = (bc - ac) and ((bc - ac) // abs(bc - ac))
        r, c = ar + dr, ac + dc
        while (r, c) != (br, bc):
            if (r, c) in self.pos:
                return False
            r, c = r + dr, c + dc
        return True

    def _process_input(self, cmd: Command):
        mover = self.piece_by_id.get(cmd.piece_id)
        if not mover:
            print(f"[DBG] unknown piece id {cmd.piece_id}")
            return

        now_ms = self.game_time_ms()

        # ---- 1. choose the *candidate* state for rules & sprites -------------
        candidate_state = mover.state.transitions.get(cmd.type, mover.state)
        moveset = candidate_state.moves  # rules for Move / Jump / Idle

        # ---- 2. legality checks ---------------------------------------------
        src = mover.state.physics.start_cell
        dest = cmd.params[0]

        legal_offset = dest in moveset.get_moves(*src)

        #???
        piece_type = mover.id[0]
        # extra rules only for pawns ---------------------------------------------
        if piece_type == "P":
            direction = -1 if mover.id[1] == "W" else 1  # white moves up
            dr, dc = dest[0] - src[0], dest[1] - src[1]

            forward_move = dr == direction and dc == 0
            diagonal_move = dr == direction and abs(dc) == 1
            occupant = self.pos.get(dest)

            if forward_move:
                # pawn can advance only into an empty square
                legal_offset = legal_offset and occupant is None
            elif diagonal_move:
                # pawn can capture only if an enemy occupies the square
                legal_offset = legal_offset and occupant is not None \
                               and occupant.id[1] != mover.id[1]
            else:
                legal_offset = False
        # ------------------------------------------------------------------------

        occupant = self.pos.get(dest)
        friendly_block = (
                occupant is not None  # a piece is there
                and occupant is not mover  # ← restore this condition
                and occupant.id[1] == mover.id[1]
        )

        # (optional) clear-path test for rook/bishop/queen
        path_clear = True
        if mover.id[0] in ("R", "B", "Q"):  # straight / diagonal sliders
            path_clear = self._path_is_clear(src, dest)

        print(f"[DBG] {cmd.type} {src}->{dest}  "
              f"offset_ok={legal_offset}  friend={friendly_block}  clear={path_clear}")

        # ---- 3. outcome ------------------------------------------------------
        if legal_offset and path_clear and not friendly_block:
            # use the candidate state (this switches sprites & physics)
            mover.state = candidate_state
            mover.state.reset(cmd)  # sets new cooldown & physics
            print(f"[EXEC] {mover.id} performs {cmd.type}")
        else:
            # illegal: stay / go back to idle sprites (no movement)
            mover.state.reset(Command(now_ms, mover.id, "Idle", []))
            print("[FAIL] move rejected")

    # ─── capture resolution ────────────────────────────────────────────────
    def _resolve_collisions(self):
        occupied: Dict[Tuple[int, int], List[Piece]] = {}
        for p in self.pieces:
            cell = p.state.physics.start_cell
            occupied.setdefault(cell, []).append(p)

        for cell, plist in occupied.items():
            if len(plist) < 2:
                continue
            # pick winner = earliest command timestamp
            winner = max(plist, key=lambda pc: pc.state.physics.start_ms)

            for p in plist:
                if p is not winner and p.state.physics.can_be_captured():
                    self.pieces.remove(p)

    # ─── board validation & win detection ───────────────────────────────────
    def _validate(self, pieces: List[Piece]) -> bool:
        seen_cells = set()
        has_white_king = has_black_king = False
        for p in pieces:
            cell = p.state.physics.start_cell
            if cell in seen_cells:
                return False
            seen_cells.add(cell)
            if p.id.startswith("KW"): has_white_king = True
            if p.id.startswith("KB"): has_black_king  = True
        return has_white_king and has_black_king

    def _is_win(self) -> bool:
        kings = [p for p in self.pieces if p.id.startswith(("KW", "KB"))]
        return len(kings) < 2

    def _announce_win(self):
        text = "Black wins!" if any(p.id.startswith("KB") for p in self.pieces) else "White wins!"
        print(text)
