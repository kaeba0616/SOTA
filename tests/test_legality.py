from sota.model.grid import Grid
from sota.solve.legality import is_legal_cell, legal_cells

G = Grid(36)

def _t(restriction):
    return {"restriction": restriction}

def test_no_restriction_anywhere():
    assert is_legal_cell(_t(None), 3, 3, G)

def test_top_only_row_0():
    assert is_legal_cell(_t("top"), 0, 4, G)
    assert not is_legal_cell(_t("top"), 1, 4, G)

def test_bottom_only_last_row():
    assert is_legal_cell(_t("bottom"), 5, 0, G)
    assert not is_legal_cell(_t("bottom"), 4, 0, G)

def test_left_right_edge_columns():
    assert is_legal_cell(_t("left_right"), 2, 0, G)
    assert is_legal_cell(_t("left_right"), 2, 5, G)
    assert not is_legal_cell(_t("left_right"), 2, 3, G)

def test_legal_cells_subset_of_grid():
    cells = legal_cells(_t("bottom"), Grid(34))
    assert cells and all(c[0] == Grid(34).rows - 1 for c in cells)
    assert (5, 4) not in cells
