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
- **All shape effects verified (2026-06-02):**
  - `row` = the tablet's whole row (`base`/기반 boosted only its row).
  - `column` = the tablet's whole column (`justice`/정의 + /large tooltip).
  - `top` = inventory top edge (row 0); `bottom` = inventory bottom edge (last row).
    `boundary`(경계, top+bottom) at (2,2) of a 6-row grid boosted row 0 and row 5 but
    NOT row 4 — so top/bottom are absolute edges, not ±offsets. Matches the code.
  - `diagonal` = the **anti-diagonal "/" line only** (`r+c` constant), NOT both diagonals.
    `rebellion`(반항) at (2,2) boosted (3,1)/(1,3)/(0,4)/(4,0) but left (1,1) at 0.
    **Fixed** in `shape_cells` (was both diagonals). Locked by golden test.
- **Clamp** holds: fire_bolt (real max 2) boosted past its cap stayed at level 2 (badge `1 / 1`).

## Resolved bug: `max_level` for 25 artifacts

Originally `max_level` came from the slash-ladder length, which is wrong for the 25
`[고유]` (spell/summon) artifacts that have no/partial ladder — e.g. `golden_hand_bell`
(was 1, real 9), `fire_bolt` (1→2), `blessing` (1→3). The wiki `level` field is the
authority. Fixed in `scrape/artifact_parse.normalize_artifact` (`max_level = level + 1`,
ladder length kept only for `scale_groups`); `artifacts.json` regenerated. For the 223
ladder artifacts `level+1` already equalled the ladder length, so they are unchanged.
This was a real optimizer bug: it under-credited boosting those 25 artifacts.

## Resolved: `restriction` placement legality

The simulator itself does NOT enforce `restriction` (a bottom-restricted `linear` could be
dropped onto row 0), but **the actual game DOES enforce it** (confirmed by the player,
2026-06-02): restricted tablets may only be placed at their designated edge —
`bottom`→last row, `top`→row 0, `left_right`→leftmost/rightmost column. So
`solve/legality.py` (which enforces exactly this) is **correct**; the simulator is just a
lenient planning tool. No code change.

## Still provisional (low impact)

- **`restriction_remove`** tablet interactions — not modeled in v1.
- **diagonal rotation** — `rebellion` is modeled at its default "/" orientation; if it is
  rotatable, other rotations (e.g. "\") are not yet handled (only 1 diagonal tablet).

## Oracle harness

Drag-drop via a dnd-kit pointer sequence works headlessly; the slab/artifact palettes are
filtered with the search box and surfaced for dragging; placed-artifact badges are read
from the grid cell text. See the session history for the exact JS. Golden deltas are
locked in `tests/test_oracle_golden.py` + `tests/fixtures/golden_deltas.json`.
