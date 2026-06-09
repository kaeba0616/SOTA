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


# Odd rotations (90/270 deg) swap row<->column and flip the anti-diagonal to
# the main diagonal; even rotations (0/180) leave a centre-line unchanged.
# Verified against the wiki bundle (rebellion/transition/agglutination/sheen).
_ROT_SHAPE = {"row": "column", "column": "row",
              "diagonal": "main_diagonal", "main_diagonal": "diagonal"}


def shape_cells(shape, trow, tcol, grid, rotation=0):
    """Cells a shape (area) effect from a tablet at (trow,tcol) hits. In-bounds only.

    Semantics (verified against the simulator oracle 2026-06-02):
      row     -> the tablet's whole row
      column  -> the tablet's whole column
      diagonal-> the ANTI-diagonal line through the tablet (r+c constant),
                 NOT both diagonals (rebellion's pattern: only "/" lights up)
      top     -> the inventory's top edge row (row 0)
      bottom  -> the inventory's bottom edge row (grid.rows - 1)

    Rotation (tablet rotation 0-3): for odd rotations a row becomes a column and
    the anti-diagonal becomes the main diagonal. top/bottom are absolute
    inventory edges and do not rotate (their tablets are non-rotatable).
    """
    if rotation % 2 == 1:
        shape = _ROT_SHAPE.get(shape, shape)
    out = []
    if shape == "row":
        out = [(trow, c) for c in range(grid.cols)]
    elif shape == "column":
        out = [(r, tcol) for r in range(grid.rows)]
    elif shape == "diagonal":
        for r in range(grid.rows):
            for c in range(grid.cols):
                if (r, c) != (trow, tcol) and (r + c) == (trow + tcol):
                    out.append((r, c))
    elif shape == "main_diagonal":
        for r in range(grid.rows):
            for c in range(grid.cols):
                if (r, c) != (trow, tcol) and (r - c) == (trow - tcol):
                    out.append((r, c))
    elif shape == "top":
        out = [(0, c) for c in range(grid.cols)]
    elif shape == "bottom":
        # The bottom EDGE is the lowest valid cell in each column. On a ragged
        # last row, columns past the last row's width drop to the row above
        # (matches the wiki 'boundary' overhang handling).
        for c in range(grid.cols):
            for r in range(grid.rows - 1, -1, -1):
                if grid.is_valid(r, c):
                    out.append((r, c))
                    break
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
                targets = shape_cells(eff["shape"], tp.row, tp.col, grid, tp.rotation)
            else:
                t = pos_target(tp.row, tp.col, eff["pos"], tp.rotation, grid)
                targets = [t] if t else []
            for cell in targets:
                deltas[cell] += eff["value"]
    return dict(deltas)
