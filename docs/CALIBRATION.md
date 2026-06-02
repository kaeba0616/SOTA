# Mechanic Calibration Notes

Verification of the evaluation-engine mechanics against the wiki simulator oracle
(`https://www.sephiria.wiki/simulator`, v0.12.0). Calibration run completed 2026-06-02.

The simulator renders, on each placed artifact, a badge **`X / Y`**.

## Confirmed (verified against the oracle)

- **`X` = total tablet level boost on that cell** = `evaluate.effects.level_deltas`.
  - Unboosted artifacts read `0 / Y`; `peace` (`[-1,0]+3 / [1,0]+3`) makes a neighbour read `3 / Y`.
  - Confirms the up-positive coordinate convention (`pos=[dx,dy]`, dy up).
- **`Y` = maximum boost = the raw wiki `level` field** (measured Y matched `level` exactly
  for fire_bolt 1, ohia_lehua 2, criton 2, ignition 3, …).
- **Start level = 1; effective level = clamp(1 + boost, 1, max_level).**
- **`max_level = level + 1`** (RESOLVED — see below).
- **`row` shape = the tablet's whole row.** Placing `base`(기반, row +1) boosted every
  artifact sharing its row by +1 and left other rows at 0. (`column` is the transpose;
  same code path.)
- **Clamp** holds: fire_bolt (real max 2) boosted past its cap stayed at level 2 (badge `1 / 1`).

## Resolved bug: `max_level` for 25 artifacts

Originally `max_level` came from the slash-ladder length, which is wrong for the 25
`[고유]` (spell/summon) artifacts that have no/partial ladder — e.g. `golden_hand_bell`
(was 1, real 9), `fire_bolt` (1→2), `blessing` (1→3). The wiki `level` field is the
authority. Fixed in `scrape/artifact_parse.normalize_artifact` (`max_level = level + 1`,
ladder length kept only for `scale_groups`); `artifacts.json` regenerated. For the 223
ladder artifacts `level+1` already equalled the ladder length, so they are unchanged.
This was a real optimizer bug: it under-credited boosting those 25 artifacts.

## Still provisional (low impact)

- **`diagonal` / `top` / `bottom` shapes** — only 4 tablets use these (1 diagonal, 1 top,
  2 bottom). `row` and the coordinate system are confirmed, giving high confidence in
  `column`; `diagonal/top/bottom` cell sets remain best-guess in
  `evaluate/effects.py:shape_cells`. Verify by placing `rebellion`(diagonal), `shade`(bottom),
  `boundary`(top/bottom) and reading which neighbour badges light up.
- **`restriction` placement legality** (`top`/`bottom`/`left_right`) in
  `solve/legality.py` — provisional; not yet oracle-checked.
- **`restriction_remove`** tablet interactions — not modeled in v1.

## Oracle harness

Drag-drop via a dnd-kit pointer sequence works headlessly; the slab/artifact palettes are
filtered with the search box and surfaced for dragging; placed-artifact badges are read
from the grid cell text. See the session history for the exact JS. Golden deltas are
locked in `tests/test_oracle_golden.py` + `tests/fixtures/golden_deltas.json`.
