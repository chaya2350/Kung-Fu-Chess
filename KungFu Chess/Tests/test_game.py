import pathlib, pytest
from unittest.mock import MagicMock
from Command import Command
from Board   import Board
from Game    import Game, InvalidBoard


# ── dummy objects ��������������������������������������������������������
class DummyPhysics:
    def __init__(self, cell): self.start_cell=cell; self.start_ms=0
    def can_be_captured(self): return True
    def reset(self,cmd):                       # allow idle reset with no params
        if cmd.params: self.start_cell=cmd.params[0]; self.start_ms=cmd.timestamp

class DummyMoves:                               # returns hard‑coded set
    def __init__(self,lst=None): self._lst=set(lst or [])
    def get_moves(self,*_): return self._lst

class DummyState:
    def __init__(self,cell,legal_moves=()):
        self.physics = DummyPhysics(cell)
        self.moves   = DummyMoves(legal_moves)
        self.transitions={}
        self.cooldown_end_ms=0
    def can_transition(self,_): return True
    def reset(self,cmd): self.physics.reset(cmd)
    def get_state_after_command(self,cmd,now_ms): return self

class DummyPiece:
    def __init__(self,pid,cell,legal_moves=()):
        self.id=pid
        self.state=DummyState(cell,legal_moves)
    def reset(self, *_): ...
    def update(self,*_): ...
    def draw_on_board(self,*_): ...

# ------------------------------------------------------------------------
def board():
    m=MagicMock(); m.img=MagicMock()
    return Board(100,100,8,8,m)

def test_invalid_duplicate_piece_positions():
    b=board()
    kw=DummyPiece("KW_a",(0,0)); kb=DummyPiece("KB_b",(0,0))
    with pytest.raises(InvalidBoard):
        Game([kw,kb],b)

def test_invalid_missing_king():
    b=board()
    p=DummyPiece("PW_x",(1,1))
    with pytest.raises(InvalidBoard):
        Game([p],b)

def test_valid_initialization():
    b=board()
    g=Game([DummyPiece("KW_a",(0,0)),DummyPiece("KB_b",(7,7))],b)
    assert isinstance(g,Game)

def test_game_time_ms_is_non_negative():
    g=Game([DummyPiece("KW_a",(0,0)),DummyPiece("KB_b",(7,7))],board())
    assert g.game_time_ms()>=0

def test_valid_command_executes():
    b=board()
    kw=DummyPiece("KW_a",(0,0),legal_moves=[(1,1)])
    g =Game([kw,DummyPiece("KB_b",(7,7))],b)
    g.pos={}; g.piece_by_id[kw.id]=kw
    cmd=Command(500,kw.id,"Move",[(1,1)])
    g._process_input(cmd)
    assert kw.state.physics.start_cell==(1,1)

def test_invalid_command_blocked_by_cooldown():
    b=board()
    kw=DummyPiece("KW_a",(0,0))
    kb=DummyPiece("KB_b",(7,7))
    g=Game([kw,kb],b)
    kw.state.cooldown_end_ms=9999
    g.piece_by_id[kw.id]=kw
    g._process_input(Command(500,kw.id,"Move",[(1,1)]))
    assert kw.state.physics.start_cell==(0,0)

def test_command_blocked_by_friendly_occupancy():
    b=board()
    kw=DummyPiece("KW_a",(0,0),legal_moves=[(1,1)])
    pawn=DummyPiece("PW_a",(1,1))
    kb=DummyPiece("KB_b",(7,7))
    g=Game([kw,pawn,kb],b)
    g.pos={(1,1):pawn}
    g._process_input(Command(100,kw.id,"Move",[(1,1)]))
    assert kw.state.physics.start_cell==(0,0)

def test_win_condition_triggers_correctly():
    b=board()
    kw=DummyPiece("KW_a",(0,0))
    kb=DummyPiece("KB_b",(7,7))
    g=Game([kw,kb],b)
    g.pieces=[kw]              # simulate capture
    assert g._is_win()

def test_win_condition_false_when_both_kings_alive():
    g=Game([DummyPiece("KW_a",(0,0)),DummyPiece("KB_b",(7,7))],board())
    assert not g._is_win()
