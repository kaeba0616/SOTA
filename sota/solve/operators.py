def tournament_select(population, scores, k, rng):
    """Return the genome (by reference) with the best score among k random picks."""
    idxs = [rng.randrange(len(population)) for _ in range(k)]
    best = max(idxs, key=lambda i: scores[i])
    return population[best]

def crossover(g1, g2, rng):
    """Uniform crossover: each gene taken from g1 or g2."""
    return [g1[i] if rng.random() < 0.5 else g2[i] for i in range(len(g1))]

def mutate(genome, n_cells, rng, rate):
    """Per-gene mutation: with prob `rate`, replace the gene with a new
    (cell, rotation): cell becomes a random cell index or None; rotation random."""
    out = []
    for cell, rot in genome:
        if rng.random() < rate:
            op = rng.random()
            if op < 0.2:
                cell = None
            else:
                cell = rng.randrange(n_cells)
            rot = rng.randint(0, 3)
        out.append((cell, rot))
    return out
