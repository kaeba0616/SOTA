import random
from dataclasses import dataclass
from sota.model.grid import Grid
from sota.solve.init import random_genome
from sota.solve.genome import decode
from sota.solve.fitness import fitness
from sota.solve.operators import tournament_select, crossover, mutate
from sota.evaluate.score import score_layout, ScoreResult

@dataclass(frozen=True)
class SolveResult:
    layout: object
    score: int
    detail: ScoreResult
    history: list

def solve(pool, target_combo, slot_count, gamedata, *, seed=0,
          generations=60, pop_size=40, tournament_k=3, elite=2,
          mutation_rate=0.15, patience=15):
    rng = random.Random(seed)
    grid = Grid(slot_count)
    n_cells = slot_count

    def score(g):
        return fitness(g, pool, grid, target_combo, gamedata)

    population = [random_genome(pool, grid, rng, gamedata) for _ in range(pop_size)]
    scores = [score(g) for g in population]
    best_i = max(range(pop_size), key=lambda i: scores[i])
    best_genome, best_score = population[best_i], scores[best_i]
    history, stale = [best_score], 0

    for _ in range(generations):
        order = sorted(range(pop_size), key=lambda i: scores[i], reverse=True)
        new_pop = [population[order[j]] for j in range(min(elite, pop_size))]
        while len(new_pop) < pop_size:
            p1 = tournament_select(population, scores, tournament_k, rng)
            p2 = tournament_select(population, scores, tournament_k, rng)
            child = mutate(crossover(p1, p2, rng), n_cells, rng, mutation_rate)
            new_pop.append(child)
        population = new_pop
        scores = [score(g) for g in population]
        gen_best_i = max(range(pop_size), key=lambda i: scores[i])
        if scores[gen_best_i] > best_score:
            best_score, best_genome, stale = scores[gen_best_i], population[gen_best_i], 0
        else:
            stale += 1
        history.append(best_score)
        if stale >= patience:
            break

    layout = decode(best_genome, pool, grid, gamedata)
    detail = score_layout(layout, target_combo, gamedata)
    return SolveResult(layout=layout, score=best_score, detail=detail, history=history)
