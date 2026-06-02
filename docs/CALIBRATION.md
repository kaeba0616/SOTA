# Mechanic Calibration Notes

Status of the evaluation-engine mechanics against the wiki simulator oracle
(`https://www.sephiria.wiki/simulator`, v0.12.0), captured 2026-06-02.

The simulator lets you drag tablets + artifacts onto the grid and renders, on each
placed artifact, a badge of the form **`X / Y`**.

## Confirmed

- **Drag-drop placement works** programmatically (dnd-kit pointer sequence).
- **Badge first number `X` = the total tablet level boost on that cell.**
  - Unboosted artifact (fire_bolt) → `0 / 1`.
  - ohia_lehua with a `peace` tablet (`[-1,0]+3 / [1,0]+3`) on its right neighbour → `3 / 2`.
  - This validates `evaluate.effects.level_deltas` (peace contributes +3) **and** the
    up-positive coordinate convention (`pos=[dx,dy]`, dy up). Locked by
    `tests/test_oracle_golden.py` + `tests/fixtures/golden_deltas.json`.

## Open (provisional in code, NOT yet oracle-verified)

These are isolated in `evaluate/levels.py` and `evaluate/effects.py:shape_cells` so they
can be corrected in one place without touching the score logic.

1. **Badge second number `Y` (base level) — meaning unknown.**
   fire_bolt → `Y=1`, ohia_lehua → `Y=2`. It is **not** `max_level`
   (ohia max_level=3) and **not** the raw wiki `level` field (which we dropped during
   scraping and which ranged 0–14). The engine currently uses a uniform
   `START_LEVEL = 1`. If `Y` is a real per-artifact base level, scoring by absolute
   effective level is off by a per-artifact constant. **Note:** for *optimization*
   (ranking placements of a fixed artifact set) a constant per-artifact offset does not
   change the argmax; it matters only for the clamp interaction below and for absolute
   score reporting.

2. **Clamp semantics.** ohia_lehua showed `3 / 2` with a +3 boost and `max_level` 3 —
   the relationship between `base (Y)`, `boost (X)`, `max_level`, and the value actually
   used is unconfirmed. `effective_level` currently does `clamp(1 + delta, 1, max_level)`.

3. **Shape effect geometry** (`row / column / diagonal / top / bottom`) — implemented as
   best-guess (whole row / whole column / both diagonals / row 0 / last row). Not yet
   placed in the simulator to confirm which cells light up.

4. **`START_LEVEL`** — provisional 1.

## How to close the open items

Re-run the simulator oracle (the drag-drop harness in the session history works): place
a single scaling artifact alone (reads base `Y` and `X=0`), then add one tablet of each
shape and read which neighbour badges change. Capture as `expected_deltas` /
`expected_levels` fixtures and tighten `test_oracle_golden.py`. If `Y` proves to be a
real base level, re-scrape artifacts to restore the per-artifact base and make
`START_LEVEL` per-artifact.
