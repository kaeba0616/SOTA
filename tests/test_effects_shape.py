from sota.evaluate.effects import shape_cells
from sota.model.grid import Grid

G = Grid(36)

def test_row_and_column():
    assert sorted(shape_cells("row", 2, 3, G)) == [(2, c) for c in range(6)]
    assert sorted(shape_cells("column", 2, 3, G)) == [(r, 3) for r in range(6)]

def test_diagonal_excludes_self():
    cells = set(shape_cells("diagonal", 2, 2, G))
    assert (2, 2) not in cells
    assert (0, 0) in cells and (4, 4) in cells
    assert (0, 4) in cells and (4, 0) in cells
    assert (2, 3) not in cells

def test_top_and_bottom_rows():
    assert sorted(shape_cells("top", 3, 1, G)) == [(0, c) for c in range(6)]
    assert sorted(shape_cells("bottom", 3, 1, G)) == [(5, c) for c in range(6)]

def test_partial_grid_excludes_invalid_cells():
    g = Grid(34)
    assert (5, 4) not in set(shape_cells("column", 0, 4, g))
