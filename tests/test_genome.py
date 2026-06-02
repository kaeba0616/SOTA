from sota.model.grid import Grid
from sota.model.pool import ItemPool
from sota.model.gamedata import load_game_data
from sota.solve.genome import decode

GD = load_game_data()

def test_decode_places_and_repairs_collisions():
    pool = ItemPool(tablets=["peace"], artifacts=["fire_bolt", "ohia_lehua"])
    grid = Grid(12)
    genome = [(7, 0), (6, 0), (6, 0)]  # candidates: peace, fire_bolt, ohia_lehua; ohia collides on cell 6
    lay = decode(genome, pool, grid, GD)
    assert any(t.key == "peace" and (t.row, t.col) == (1, 1) for t in lay.tablets)
    assert any(a.key == "fire_bolt" and (a.row, a.col) == (1, 0) for a in lay.artifacts)
    assert all(a.key != "ohia_lehua" for a in lay.artifacts)

def test_decode_drops_unplaced_and_illegal():
    pool = ItemPool(tablets=["linear"], artifacts=[])  # linear restriction 'bottom'
    grid = Grid(12)  # rows = 2; bottom row index 1
    assert decode([(None, 0)], pool, grid, GD).tablets == []
    assert decode([(0, 0)], pool, grid, GD).tablets == []        # row 0 illegal for 'bottom'
    assert len(decode([(grid.index(1, 0), 0)], pool, grid, GD).tablets) == 1
