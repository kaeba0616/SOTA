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

## Open question: `restriction` placement legality

**The simulator does NOT enforce tablet `restriction`.** `linear`(선의, restriction
`bottom`) dropped onto row 0 stayed there — a bottom-restricted tablet placed at the top.
So the score oracle is permissive: restricted tablets can sit anywhere and still compute.

`solve/legality.py` currently FORBIDS restricted tablets outside their edge (bottom→last
row, top→row 0, left_right→edge columns), derived from the /large tooltip ★ positions.
This is **stricter than the simulator**. Two possibilities:
- The actual game enforces the restriction (then the constraint is correct and the
  simulator is just a lenient planning tool) — keep `legality` as is.
- The game is also permissive (then `legality` is over-restrictive and the GA misses
  valid layouts) — relax it.

**Needs the player's confirmation** (can 선의/정의/차양 be placed anywhere in-game, or only
at the bottom/edge/top?). Until then `legality` stays conservative (enforced), so suggested
layouts are guaranteed legal even if some valid ones are skipped. Affects only 3 tablets.

## Still provisional (low impact)

- **`restriction_remove`** tablet interactions — not modeled in v1.
- **diagonal rotation** — `rebellion` is modeled at its default "/" orientation; if it is
  rotatable, other rotations (e.g. "\") are not yet handled (only 1 diagonal tablet).

## Oracle harness

Drag-drop via a dnd-kit pointer sequence works headlessly; the slab/artifact palettes are
filtered with the search box and surfaced for dragging; placed-artifact badges are read
from the grid cell text. See the session history for the exact JS. Golden deltas are
locked in `tests/test_oracle_golden.py` + `tests/fixtures/golden_deltas.json`.
