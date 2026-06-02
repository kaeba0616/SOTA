from sota.solve.legality import is_legal_cell

def random_genome(pool, grid, rng, gamedata, place_prob=0.85):
    """Random valid-ish genome: each candidate gets a random distinct legal cell
    (or None). Tablets only get cells legal for their restriction.

    Determinism guarantee: `free` is maintained as a sorted list so that the
    linear scan for a legal cell always visits cells in the same order
    regardless of prior removals, making g1 == g2 for equal seeds.
    """
    cands = pool.candidates()
    # Sorted list of free cell indices; sort gives a stable, seed-independent order.
    free = sorted(grid.index(r, c) for (r, c) in grid.cells())
    rng.shuffle(free)
    # Re-sort after shuffle to restore a deterministic scan order independent of
    # which cells have been removed.  We track availability via a set for O(1)
    # membership, but always scan sorted_free for selection order.
    available = set(free)
    sorted_free = sorted(available)

    genome = []
    for kind, key in cands:
        if not available or rng.random() > place_prob:
            genome.append((None, rng.randint(0, 3)))
            continue
        tablet = gamedata.tablets.get(key) if kind == "tablet" else None
        choice = None
        for cell in sorted_free:
            if cell not in available:
                continue
            r, c = divmod(cell, grid.cols)
            if tablet is None or is_legal_cell(tablet, r, c, grid):
                choice = cell
                break
        if choice is None:
            genome.append((None, rng.randint(0, 3)))
        else:
            available.discard(choice)
            genome.append((choice, rng.randint(0, 3)))
    return genome
