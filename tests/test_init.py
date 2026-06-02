import random
from sota.model.grid import Grid
from sota.model.pool import ItemPool
from sota.model.gamedata import load_game_data
from sota.solve.init import random_genome
from sota.solve.genome import decode

GD = load_game_data()

def test_random_genome_is_deterministic_and_valid():
    pool = ItemPool(tablets=["peace", "linear"], artifacts=["fire_bolt", "ohia_lehua"])
    grid = Grid(12)
    g1 = random_genome(pool, grid, random.Random(42), GD)
    g2 = random_genome(pool, grid, random.Random(42), GD)
    assert g1 == g2
    assert len(g1) == len(pool)
    lay = decode(g1, pool, grid, GD)
    cells = [(t.row, t.col) for t in lay.tablets] + [(a.row, a.col) for a in lay.artifacts]
    assert len(cells) == len(set(cells))

def test_more_items_than_slots_leaves_some_unplaced():
    pool = ItemPool(tablets=[], artifacts=["fire_bolt"] * 10)
    grid = Grid(4)
    g = random_genome(pool, grid, random.Random(1), GD)
    lay = decode(g, pool, grid, GD)
    assert len(lay.artifacts) <= 4
