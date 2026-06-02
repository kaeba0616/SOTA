from sota.model.grid import Grid
from sota.model.layout import Layout, TabletPlacement, ArtifactPlacement
from sota.model.gamedata import load_game_data
from sota.evaluate.effects import level_deltas
from sota.evaluate.levels import effective_level, START_LEVEL

GD = load_game_data()

def test_peace_adds_to_both_horizontal_neighbors():
    g = Grid(12)
    lay = Layout(slot_count=12,
                 tablets=[TabletPlacement("peace", 1, 1, 0)],
                 artifacts=[])
    d = level_deltas(lay, g, GD)
    assert d[(1, 0)] == 3
    assert d[(1, 2)] == 3
    assert (0, 1) not in d

def test_negative_does_not_stack_when_targets_differ():
    # advent was replaced: advent has 4 effects that cancel across two placements.
    # sight has pos=[1,-1] (dx=1,dy=-1) -> target(trow+1, tcol+1) value=-1.
    # sight at (0,0): target (1,1)=-1.  sight at (2,0): target (3,1)=-1. No overlap.
    g = Grid(24)
    lay = Layout(slot_count=24,
                 tablets=[TabletPlacement("sight", 0, 0, 0),
                          TabletPlacement("sight", 2, 0, 0)],
                 artifacts=[])
    d = level_deltas(lay, g, GD)
    assert d[(1, 1)] == -1
    assert d[(3, 1)] == -1

def test_effective_level_clamps_to_max():
    art = {"max_level": 4}
    assert effective_level(art, 0) == START_LEVEL
    assert effective_level(art, 2) == 3
    assert effective_level(art, 99) == 4
    assert effective_level(art, -99) == 1
