import random
from sota.solve.operators import tournament_select, crossover, mutate

def test_tournament_picks_higher_score():
    pop = [["a"], ["b"], ["c"]]
    scores = [10, 50, 30]
    rng = random.Random(0)
    winners = [tournament_select(pop, scores, k=3, rng=rng) for _ in range(5)]
    assert all(w == ["b"] for w in winners)

def test_crossover_mixes_genes_same_length():
    g1 = [(1, 0), (2, 0), (3, 0)]
    g2 = [(9, 1), (8, 1), (7, 1)]
    child = crossover(g1, g2, random.Random(1))
    assert len(child) == 3
    assert all(child[i] in (g1[i], g2[i]) for i in range(3))

def test_crossover_deterministic_with_seed():
    g1, g2 = [(1, 0)], [(2, 1)]
    assert crossover(g1, g2, random.Random(5)) == crossover(g1, g2, random.Random(5))

def test_mutate_changes_at_least_one_gene_at_full_rate():
    genome = [(0, 0), (1, 0), (2, 0)]
    out = mutate(genome, n_cells=12, rng=random.Random(3), rate=1.0)
    assert len(out) == 3
    assert out != genome
    for cell, rot in out:
        assert cell is None or 0 <= cell < 12
        assert 0 <= rot <= 3
