from dataclasses import dataclass

from img import Img

@dataclass
class Board:
    cell_H_pix: int
    cell_W_pix: int
    W_cells: int
    H_cells: int
    img: Img

    # convenience, not required by dataclass
    def clone(self) -> "Board":
        new_img = Img()
        new_img.img = self.img.img.copy()
        return Board(self.cell_H_pix, self.cell_W_pix,
                     self.W_cells,    self.H_cells,
                     new_img)

