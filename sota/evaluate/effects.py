from collections import defaultdict


def rotate_pos(pos, rotation):
    """Rotate [dx, dy] (dx right+, dy up+) by rotation*90 deg clockwise."""
    dx, dy = pos
    for _ in range(rotation % 4):
        dx, dy = dy, -dx
    return (dx, dy)


def pos_target(trow, tcol, pos, rotation, grid):
    """Cell a pos effect from a tablet at (trow,tcol) targets, or None if off-grid."""
    dx, dy = rotate_pos(pos, rotation)
    r, c = trow - dy, tcol + dx
    return (r, c) if grid.is_valid(r, c) else None


def shape_cells(shape, trow, tcol, grid):
    """Cells a shape (area) effect from a tablet at (trow,tcol) hits. In-bounds only.

    Provisional semantics (verified against the simulator oracle in Task 8):
      row     -> the tablet's whole row
      column  -> the tablet's whole column
      diagonal-> both diagonals through the tablet (excludes the tablet cell)
      top     -> the topmost row (row 0)
      bottom  -> the bottommost occupied row (grid.rows - 1)
    """
    out = []
    if shape == "row":
        out = [(trow, c) for c in range(grid.cols)]
    elif shape == "column":
        out = [(r, tcol) for r in range(grid.rows)]
    elif shape == "diagonal":
        for r in range(grid.rows):
            for c in range(grid.cols):
                if (r, c) != (trow, tcol) and abs(r - trow) == abs(c - tcol):
                    out.append((r, c))
    elif shape == "top":
        out = [(0, c) for c in range(grid.cols)]
    elif shape == "bottom":
        out = [(grid.rows - 1, c) for c in range(grid.cols)]
    else:
        raise ValueError(f"unknown shape {shape}")
    return [(r, c) for (r, c) in out if grid.is_valid(r, c)]


def level_deltas(layout, grid, gamedata):
    """Per-cell total level_add delta from all tablets' effects (pos + shape)."""
    deltas = defaultdict(int)
    for tp in layout.tablets:
        tablet = gamedata.tablets.get(tp.key)
        if tablet is None:
            continue
        for eff in tablet["effects"]:
            if eff.get("type") != "level_add":
                continue
            if "shape" in eff:
                targets = shape_cells(eff["shape"], tp.row, tp.col, grid)
            else:
                t = pos_target(tp.row, tp.col, eff["pos"], tp.rotation, grid)
                targets = [t] if t else []
            for cell in targets:
                deltas[cell] += eff["value"]
    return dict(deltas)
