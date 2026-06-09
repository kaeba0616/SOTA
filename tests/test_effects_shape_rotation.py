"""Shape effects must rotate with the tablet (verified against the wiki bundle).

Wiki logic: for rotation 1 or 3 (90/270 deg) a row becomes a column and the
anti-diagonal ("/") becomes the main diagonal ("\\"); rotation 0/2 unchanged
(a line through the centre is symmetric under 180 deg).
"""
from sota.model.grid import Grid
from sota.model.layout import Layout, TabletPlacement
from sota.evaluate.effects import shape_cells, level_deltas
from sota.model.gamedata import load_game_data

G = Grid(36)
GD = load_game_data()


def test_row_becomes_column_at_90():
    assert sorted(shape_cells("row", 2, 2, G, 1)) == [(r, 2) for r in range(6)]
    assert sorted(shape_cells("column", 2, 2, G, 1)) == [(2, c) for c in range(6)]


def test_row_unchanged_at_0_and_180():
    row2 = [(2, c) for c in range(6)]
    assert sorted(shape_cells("row", 2, 2, G, 0)) == row2
    assert sorted(shape_cells("row", 2, 2, G, 2)) == row2


def test_diagonal_flips_to_main_at_90():
    anti = set(shape_cells("diagonal", 2, 2, G, 0))   # r+c == 4
    main = set(shape_cells("diagonal", 2, 2, G, 1))   # r-c == 0
    assert (0, 4) in anti and (4, 0) in anti
    assert (0, 0) in main and (5, 5) in main
    assert (0, 0) not in anti and (0, 4) not in main


def test_rebellion_rotation_flips_diagonal():
    def reb(rot):
        lay = Layout(slot_count=36,
                     tablets=[TabletPlacement("rebellion", 2, 2, rot)], artifacts=[])
        return set(level_deltas(lay, G, GD))
    assert (0, 4) in reb(0) and (4, 0) in reb(0)   # anti at rot 0
    assert (0, 0) in reb(1) and (5, 5) in reb(1)   # main at rot 1
