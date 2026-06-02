from PIL import Image, ImageDraw
from sota.model.grid import Grid
from sota.evaluate.effects import level_deltas
from sota.evaluate.levels import effective_level
from sota.render.icons import icon_path

_BG = (40, 30, 45)
_CELL = (70, 50, 60)
_LINE = (90, 70, 80)
_HEADER_H = 28

def render_layout(layout, target_combo, gamedata, root, cell=64):
    grid = Grid(layout.slot_count)
    w = grid.cols * cell
    h = _HEADER_H + grid.rows * cell
    img = Image.new("RGB", (w, h), _BG)
    d = ImageDraw.Draw(img)
    d.text((6, 8), f"{target_combo}", fill=(230, 220, 225))

    for (r, c) in grid.cells():
        x0, y0 = c * cell, _HEADER_H + r * cell
        d.rectangle([x0, y0, x0 + cell - 1, y0 + cell - 1], fill=_CELL, outline=_LINE)

    deltas = level_deltas(layout, grid, gamedata)

    def paste_icon(kind, key, r, c):
        p = icon_path(kind, key, root)
        x0, y0 = c * cell, _HEADER_H + r * cell
        if p is not None:
            ico = Image.open(p).convert("RGBA").resize((cell - 6, cell - 6))
            img.paste(ico, (x0 + 3, y0 + 3), ico)
        else:
            d.text((x0 + 4, y0 + 4), key[:6], fill=(220, 220, 220))

    for t in layout.tablets:
        paste_icon("tablet", t.key, t.row, t.col)
    for a in layout.artifacts:
        paste_icon("artifact", a.key, a.row, a.col)
        art = gamedata.artifacts.get(a.key)
        if art is not None:
            lvl = effective_level(art, deltas.get((a.row, a.col), 0))
            x0, y0 = a.col * cell, _HEADER_H + a.row * cell
            d.text((x0 + 3, y0 + cell - 14), f"L{lvl}", fill=(255, 235, 120))
    return img
