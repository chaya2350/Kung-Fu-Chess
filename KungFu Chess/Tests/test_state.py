import types, pytest
from Command  import Command
from State    import State

# dummy helpers ---------------------------------------------------------
class MockGraphics:
    def __init__(self): self.reset_called=False
    def reset(self, *_): self.reset_called=True
    def update(self,*_): ...
    def get_img(self):   ...

class MockPhysics:
    def __init__(self): self.reset_called=False; self.start_cell=(0,0); self.start_ms=0
    def reset(self,cmd): self.reset_called=True; self.start_cell=cmd.params[0] if cmd.params else (0,0)
    def update(self,*_): return None
    def can_be_captured(self): return True

class MockMoves:
    def get_moves(self,*_): return set()

# ----------------------------------------------------------------------
def make_state():
    return State(MockMoves(),MockGraphics(),MockPhysics())

def test_reset_sets_cooldown_move():
    st=make_state()
    cmd=Command(1000,"X","Move",[(1,1)])
    st.reset(cmd)
    # cooldown is armed only after Arrived – should be 0 right after reset
    assert st.cooldown_end_ms==0

def test_reset_sets_cooldown_jump():
    st=make_state()
    cmd=Command(2000,"X","Jump",[(0,0)])
    st.reset(cmd)
    assert st.cooldown_end_ms==0

def test_can_transition_true():
    st=make_state(); st.cooldown_end_ms=100
    assert st.can_transition(101)

def test_can_transition_false():
    st=make_state(); st.cooldown_end_ms=100
    assert not st.can_transition(99)

def test_get_state_after_command_transitions_if_allowed():
    st1=make_state(); st2=make_state()
    st1.set_transition("Move",st2)
    cmd=Command(0,"X","Move",[(1,1)])
    nxt=st1.get_state_after_command(cmd,now_ms=0)
    assert nxt is st2

def test_get_state_after_command_no_transition():
    st = make_state()
    cmd = Command(0, "X", "Move", [(1, 1)])
    nxt = st.get_state_after_command(cmd, now_ms=0)
    assert nxt is st                      # stays in same state
