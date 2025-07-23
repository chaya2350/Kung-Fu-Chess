import queue, threading, time, math, logging
from typing import List, Dict, Tuple, Optional

from Board   import Board
from Command import Command
from Piece   import Piece
from img import Img, close_all_img_windows, draw_rect

from KeyboardInput import KeyboardProcessor, KeyboardProducer

# set up a module-level logger – real apps can configure handlers/levels
logger = logging.getLogger(__name__)

class InvalidBoard(Exception): ...

class Game:
    def __init__(self, pieces: List[Piece], board: Board):
        if not self._validate(pieces):
            raise InvalidBoard("duplicate pieces or no king")
        self.pieces           = pieces
        self.board            = board
        self.START_NS         = time.monotonic_ns()
        self.user_input_queue = queue.Queue()          # thread-safe
        # fast lookup tables ---------------------------------------------------
        self.pos            : Dict[Tuple[int, int], Piece] = {}
        self.piece_by_id    : Dict[str, Piece] = {p.id: p for p in pieces}

        self.selected_id_1: Optional[str] = None
        self.selected_id_2: Optional[str] = None
        self.last_cursor2: Tuple[int, int] | None = None
        self.last_cursor1: Tuple[int, int] | None = None

        # keyboard helpers ---------------------------------------------------
        self.keyboard_processor: Optional[KeyboardProcessor] = None
        self.keyboard_producer : Optional[KeyboardProducer]  = None

    def game_time_ms(self) -> int:
        return (time.monotonic_ns() - self.START_NS) // 1_000_000

    def clone_board(self) -> Board:
        img_copy = Img()
        img_copy.img = self.board.img.img.copy()
        return Board(self.board.cell_H_pix, self.board.cell_W_pix,
                     self.board.W_cells,    self.board.H_cells,
                     img_copy)

    def start_user_input_thread(self):

        # player 1 key‐map
        p1_map = {
            "up": "up", "down": "down", "left": "left", "right": "right",
            "enter": "select", "+": "jump"
        }
        # player 2 key‐map
        p2_map = {
            "w": "up", "s": "down", "a": "left", "d": "right",
            "f": "select", "g": "jump"
        }

        # create two processors
        self.kp1 = KeyboardProcessor(self.board.H_cells,
                                     self.board.W_cells,
                                     keymap=p1_map)
        self.kp2 = KeyboardProcessor(self.board.H_cells,
                                     self.board.W_cells,
                                     keymap=p2_map)

        # **pass the player number** as the 4th argument!
        self.kb_prod_1 = KeyboardProducer(self,
                                          self.user_input_queue,
                                          self.kp1,
                                          player=1)
        self.kb_prod_2 = KeyboardProducer(self,
                                          self.user_input_queue,
                                          self.kp2,
                                          player=2)

        self.kb_prod_1.start()
        self.kb_prod_2.start()

    def run(self):
        self.start_user_input_thread()
        start_ms = self.game_time_ms()
        for p in self.pieces:
            p.reset(start_ms)

        while not self._is_win():
            now = self.game_time_ms()
            for p in self.pieces:
                p.update(now)
            while not self.user_input_queue.empty():
                cmd: Command = self.user_input_queue.get()
                self._process_input(cmd)
            self._draw()
            self._show()
            self._resolve_collisions()

        self._announce_win()
        close_all_img_windows()
        if self.kb_prod_1:
            self.kb_prod_1.stop()
            self.kb_prod_2.stop()

    def _draw(self):
        self.curr_board = self.clone_board()
        self.pos.clear()
        for p in self.pieces:
            p.draw_on_board(self.curr_board, now_ms=self.game_time_ms())
            self.pos[p.current_cell()] = p

        # overlay both players' cursors, but only log on change
        if self.kp1 and self.kp2:
            for player, kp, last in (
                (1, self.kp1, 'last_cursor1'),
                (2, self.kp2, 'last_cursor2')
            ):
                r, c = kp.get_cursor()
                # draw rectangle
                y1 = r * self.board.cell_H_pix; x1 = c * self.board.cell_W_pix
                y2 = y1 + self.board.cell_H_pix - 1; x2 = x1 + self.board.cell_W_pix - 1
                color = (0,255,0) if player==1 else (255,0,0)
                draw_rect(self.curr_board.img.img, x1, y1, x2, y2, color)
                # only print if moved
                prev = getattr(self, last)
                if prev != (r, c):
                    logger.debug("Marker P%s moved to (%s, %s)", player, r, c)
                    setattr(self, last, (r, c))

    def _show(self):
        self.curr_board.show()

    def _side_of(self, piece_id: str) -> str:
        return piece_id[1]

    def _path_is_clear(self, a, b):
        ar, ac = a; br, bc = b
        dr = (br-ar) and ((br-ar)//abs(br-ar))
        dc = (bc-ac) and ((bc-ac)//abs(bc-ac))
        r, c = ar+dr, ac+dc
        while (r,c) != (br,bc):
            if (r,c) in self.pos: return False
            r, c = r+dr, c+dc
        return True

    def _process_input(self, cmd: Command):
        mover = self.piece_by_id.get(cmd.piece_id)
        if not mover:
            logger.debug("Unknown piece id %s", cmd.piece_id)
            return

        now_ms = self.game_time_ms()
        if not mover.state.can_transition(now_ms):
            logger.debug("%s still in cooldown until %s ms", mover.id, mover.state.cooldown_end_ms)
            return

        if not mover.state.is_legal(mover, cmd, self.pos, self._path_is_clear):
            mover.state.reset(Command(now_ms, mover.id, "Idle", []))
            logger.info("Move rejected for %s to %s", mover.id, cmd.params[0])
            return

        nxt = mover.state.transitions.get(cmd.type, mover.state)
        mover.state = nxt
        mover.state.reset(cmd)
        logger.info("%s performs %s to %s", mover.id, cmd.type, cmd.params[0])

    def _resolve_collisions(self):
        occupied: Dict[Tuple[int,int], List[Piece]] = {}
        for p in self.pieces:
            cell = p.current_cell()
            occupied.setdefault(cell, []).append(p)
        for cell, plist in occupied.items():
            if len(plist)<2: continue
            winner = max(plist, key=lambda pc:pc.state.physics.start_ms)
            for p in plist:
                if p is not winner and p.state.physics.can_be_captured():
                    self.pieces.remove(p)

    def _validate(self, pieces: List[Piece]) -> bool:
        seen=set(); wking=bking=False
        for p in pieces:
            cell = p.current_cell()
            if cell in seen: return False
            seen.add(cell)
            if p.id.startswith('KW'): wking=True
            if p.id.startswith('KB'): bking=True
        return wking and bking

    def _is_win(self) -> bool:
        kings=[p for p in self.pieces if p.id.startswith(('KW','KB'))]
        return len(kings)<2

    def _announce_win(self):
        text = 'Black wins!' if any(p.id.startswith('KB') for p in self.pieces) else 'White wins!'
        logger.info(text)
