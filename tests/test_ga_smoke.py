import random
from sota.model.pool import ItemPool
from sota.model.gamedata import load_game_data
from sota.solve.ga import solve

GD = load_game_data()

def test_realistic_pool_runs_and_is_valid():
    rng = random.Random(11)
    yinggalbul = [k for k, a in GD.artifacts.items() if "yinggalbul" in a["combos"]]
    pool = ItemPool(
        tablets=rng.sample(list(GD.tablets), 8),
        artifacts=rng.sample(yinggalbul, min(8, len(yinggalbul))),
    )
    res = solve(pool, "yinggalbul", slot_count=24, gamedata=GD,
                seed=11, generations=40, pop_size=40)
    cells = [(t.row, t.col) for t in res.layout.tablets] + \
            [(a.row, a.col) for a in res.layout.artifacts]
    assert len(cells) == len(set(cells))           # no two items share a cell
    from sota.solve.legality import is_legal_cell
    from sota.model.grid import Grid
    g = Grid(24)
    assert all(is_legal_cell(GD.tablets[t.key], t.row, t.col, g) for t in res.layout.tablets)
    assert res.score >= 0
