from sota.solve.genome import decode
from sota.evaluate.score import score_layout

def fitness(genome, pool, grid, target_combo, gamedata) -> int:
    layout = decode(genome, pool, grid, gamedata)
    return score_layout(layout, target_combo, gamedata).score
