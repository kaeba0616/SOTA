def is_legal_cell(tablet, r, c, grid):
    """Whether a tablet may occupy (r,c). Provisional restriction semantics
    (see docs/CALIBRATION.md): top->row 0, bottom->last row,
    left_right->edge columns, None->anywhere."""
    if not grid.is_valid(r, c):
        return False
    restriction = tablet.get("restriction")
    if restriction is None:
        return True
    if restriction == "top":
        return r == 0
    if restriction == "bottom":
        return r == grid.rows - 1
    if restriction == "left_right":
        return c == 0 or c == grid.cols - 1
    return True

def legal_cells(tablet, grid):
    return [(r, c) for (r, c) in grid.cells() if is_legal_cell(tablet, r, c, grid)]
