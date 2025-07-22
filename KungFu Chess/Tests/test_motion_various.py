import numpy as np, pytest
from Physics  import Physics
from Command  import Command

class DummyBoard:
    def __init__(self,c=70):
        self.cell_W_pix=self.cell_H_pix=c; self.W_cells=self.H_cells=8

# numeric helpers
def max_perp_distance(pts):
    p0,pN=pts[0],pts[-1]; v=pN-p0; n=np.linalg.norm(v)
    if n<1e-9: return 0.0
    return np.max(np.abs(np.cross(v,pts-p0))/n)

def step_variation(pts):
    d=np.linalg.norm(pts[1:]-pts[:-1],axis=1)
    return d.max()-d.min()

CASES=[((1,1),(6,6)),((0,0),(0,7)),((7,7),(0,7)),((2,5),(5,2)),((3,0),(3,4))]

@pytest.mark.parametrize("start_cell,end_cell",CASES,ids=[f"{s}->{e}" for s,e in CASES])
def test_move_straight_and_uniform(start_cell,end_cell):
    phys=Physics(start_cell,DummyBoard())
    phys.reset(Command(0,"P?","Move",[end_cell]))
    samples=[]
    for t in range(0,301,30):
        phys.update(t); samples.append(np.array(phys.curr_px_f))
    pts=np.stack(samples)
    assert max_perp_distance(pts)<=1.0
    assert step_variation(pts)<=2.0
