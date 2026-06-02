from sota.model.grid import Grid
from sota.model.pool import ItemPool
from sota.model.gamedata import load_game_data
from sota.solve.fitness import fitness

GD = load_game_data()

def test_fitness_is_score_of_decoded_layout():
    pool = ItemPool(tablets=["peace"], artifacts=["fire_bolt", "ohia_lehua"])
    grid = Grid(12)
    genome = [(grid.index(0, 1), 0), (grid.index(0, 0), 0), (grid.index(0, 2), 0)]
    f = fitness(genome, pool, grid, "yinggalbul", GD)
    assert f >= 1000
