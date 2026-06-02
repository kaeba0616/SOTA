from sota.model.grid import Grid

def test_partial_last_row():
    g = Grid(34)
    assert g.cols == 6
    assert g.rows == 6
    assert g.is_valid(0, 0)
    assert g.is_valid(5, 3)
    assert not g.is_valid(5, 4)
    assert not g.is_valid(6, 0)
    assert not g.is_valid(0, -1)

def test_cells_count_equals_slot_count():
    g = Grid(34)
    assert len(list(g.cells())) == 34
    assert (5, 3) in set(g.cells())
    assert (5, 4) not in set(g.cells())
