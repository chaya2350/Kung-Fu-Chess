from Board import Board
from Physics import Physics


class PhysicsFactory:      # very light for now
    def __init__(self, board: Board): self.board = board
    def create(self, start_cell, cfg) -> Physics:
        return Physics(start_cell, self.board, cfg.get("speed_m_per_sec", 1.0))
