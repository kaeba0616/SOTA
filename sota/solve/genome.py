from sota.model.layout import Layout, TabletPlacement, ArtifactPlacement
from sota.solve.legality import is_legal_cell

def decode(genome, pool, grid, gamedata):
    """Build a valid Layout from a genome. Genes align with pool.candidates().
    Items with cell None / off-grid / occupied / (tablet) illegal are dropped."""
    cands = pool.candidates()
    taken = set()
    tablets, artifacts = [], []
    for (kind, key), gene in zip(cands, genome):
        cell, rotation = gene
        if cell is None:
            continue
        r, c = divmod(cell, grid.cols)
        if not grid.is_valid(r, c) or (r, c) in taken:
            continue
        if kind == "tablet":
            tablet = gamedata.tablets.get(key)
            if tablet is None or not is_legal_cell(tablet, r, c, grid):
                continue
            taken.add((r, c))
            rot = rotation % 4 if tablet.get("rotatable") else 0
            tablets.append(TabletPlacement(key=key, row=r, col=c, rotation=rot))
        else:
            taken.add((r, c))
            artifacts.append(ArtifactPlacement(key=key, row=r, col=c))
    return Layout(slot_count=grid.slot_count, tablets=tablets, artifacts=artifacts)
