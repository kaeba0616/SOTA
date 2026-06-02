# Evaluation Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the pure, deterministic scoring core: given a grid layout of tablets + artifacts and a target combo, compute the build score (target-combo artifact effective-levels + combo threshold stages), with all game mechanics modeled honestly and verified against the wiki simulator oracle.

**Architecture:** A set of small pure modules — game-data loader, grid geometry, layout container, effect application (pos + shape + rotation), level computation, and the objective score. No I/O, no solver. Every rule is TDD'd with analytic cases and locked against a small golden dataset captured from the simulator (which computes effective levels — confirmed). The engine is the fitness function the GA solver (sub-plan 3) will call.

**Tech Stack:** Python 3.12, pytest. Reads `sota/data/*.json` from sub-plan 1.

**This is sub-project 2 of 5.** Depends on sub-plan 1's data (`artifacts.json` 248, `combos.json` 19, `tablets.json` 54, all 1×1). Consumed by sub-plan 3 (GA solver). See `docs/superpowers/specs/2026-06-01-combo-build-optimizer-design.md` (§2 mechanics, §3 objective, §4 special artifacts, §12 oracle).

---

## Key facts (verified against sub-plan 1 data + wiki)

- All 54 tablets are **size [1,1]** → an item occupies exactly one cell.
- Grid is **6 columns**; `slot_count` N cells fill row-major; last row may be partial. A cell `(r, c)` is valid iff `r*6 + c < N`.
- Tablet effect coordinate convention (verified): `pos=[dx, dy]`, `dx` = column offset (right +), `dy` = row offset (**up +**). A tablet at `(r, c)` with pos `[dx, dy]` targets cell `(r - dy, c + dx)`.
- Two effect kinds (pos XOR shape). Shape kinds present: `row, column, diagonal, top, bottom`.
- Effect types: `level_add` (value int, may be negative) and `restriction_remove` (value bool — affects placement legality, NOT level score; the evaluator treats it as a no-op for scoring).
- Artifact `max_level` varies per artifact (= slash-ladder length, 1..15). Artifacts start at level 1; tablets raise the level.
- Combo thresholds are `[2,4,6,8,10]` for all combos; "stages reached" = how many thresholds ≤ the count of that combo's artifacts in the inventory.
- ~20 artifacts have global/positional/conditional effects (special). v1 = approximate (treat as ordinary level-scaled) + flag in the score breakdown.

## Provisional mechanics to VERIFY via oracle (Task 8)

These are implemented as best-guesses and confirmed/adjusted against the simulator in Task 8:
- **Start level = 1**, `effective = clamp(1 + Σ level_add hitting the cell, 1, max_level)`.
- **Shape semantics:** `row` = every valid cell sharing the tablet's row; `column` = every valid cell sharing the tablet's column; `diagonal` = every valid cell on either diagonal through the tablet (`|r-tr| == |c-tc|`, excluding the tablet cell); `top` = every valid cell in row 0; `bottom` = every valid cell in the last (highest-index) row that contains any cell.
- **Stacking:** multiple level_add effects on one cell sum; negatives included.
- These are isolated in `effects.py`/`levels.py` so Task 8 can correct them in one place.

---

## File Structure

```
sota/
  model/
    __init__.py
    gamedata.py      # load_game_data(data_dir) -> GameData(artifacts, tablets, combos) keyed by key
    grid.py          # Grid(slot_count): COLS=6, validity, iteration, neighbor math
    layout.py        # Placement, Layout (tablets + artifacts on a grid)
  evaluate/
    __init__.py
    effects.py       # rotate_pos, affected_cells (pos + shape), level_deltas(layout)
    levels.py        # effective_level(artifact, delta); START_LEVEL constant
    special.py       # SPECIAL_MARKERS, is_special(artifact) -> bool
    score.py         # combo_stages(), score_layout() -> ScoreResult(score, breakdown)
tests/
  fixtures/
    golden_layouts.json   # captured from simulator (Task 8)
  test_grid.py
  test_effects_pos.py
  test_effects_shape.py
  test_levels.py
  test_special.py
  test_score.py
  test_oracle_golden.py
```

---

## Task 1: Game-data loader

Loads the three JSON files into a typed container keyed by `key` for O(1) lookup.

**Files:** Create `sota/model/__init__.py` (empty), `sota/model/gamedata.py`; Test `tests/test_grid.py` is later — this task's test is inline below.

- [ ] **Step 1: Write the failing test** `tests/test_gamedata.py`

```python
from sota.model.gamedata import load_game_data

def test_loads_real_data():
    gd = load_game_data()
    assert len(gd.artifacts) == 248
    assert len(gd.tablets) == 54
    assert len(gd.combos) == 19
    assert gd.artifacts["fire_bolt"]["max_level"] == 1
    assert gd.tablets["peace"]["effects"][0]["type"] == "level_add"
    assert gd.combos["yinggalbul"]["thresholds"][0]["count"] == 2

def test_lookup_missing_returns_none():
    gd = load_game_data()
    assert gd.artifacts.get("nope") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_gamedata.py -v`
Expected: FAIL with `ModuleNotFoundError: sota.model.gamedata`.

- [ ] **Step 3: Implement** `sota/model/gamedata.py`

```python
import json, pathlib
from dataclasses import dataclass

_DATA = pathlib.Path(__file__).resolve().parents[1] / "data"

@dataclass(frozen=True)
class GameData:
    artifacts: dict   # key -> artifact dict
    tablets: dict     # key -> tablet dict
    combos: dict      # key -> combo dict

def _load(name):
    return json.loads((_DATA / name).read_text(encoding="utf-8"))

def load_game_data() -> GameData:
    return GameData(
        artifacts={a["key"]: a for a in _load("artifacts.json")},
        tablets={t["key"]: t for t in _load("tablets.json")},
        combos={c["key"]: c for c in _load("combos.json")},
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_gamedata.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add sota/model/__init__.py sota/model/gamedata.py tests/test_gamedata.py
git commit -m "feat: game-data loader keyed by key"
```

---

## Task 2: Grid geometry

6-column grid with `slot_count` cells; knows which `(row, col)` are valid.

**Files:** Create `sota/model/grid.py`; Test `tests/test_grid.py`

- [ ] **Step 1: Write the failing test**

```python
from sota.model.grid import Grid

def test_partial_last_row():
    g = Grid(34)            # 5 full rows of 6 + 4 = 34
    assert g.cols == 6
    assert g.rows == 6      # ceil(34/6)
    assert g.is_valid(0, 0)
    assert g.is_valid(5, 3)     # index 33 < 34
    assert not g.is_valid(5, 4) # index 34 not < 34
    assert not g.is_valid(6, 0)
    assert not g.is_valid(0, -1)

def test_cells_count_equals_slot_count():
    g = Grid(34)
    assert len(list(g.cells())) == 34
    assert (5, 3) in set(g.cells())
    assert (5, 4) not in set(g.cells())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_grid.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement** `sota/model/grid.py`

```python
import math

class Grid:
    cols = 6

    def __init__(self, slot_count: int):
        if slot_count < 1:
            raise ValueError("slot_count must be >= 1")
        self.slot_count = slot_count
        self.rows = math.ceil(slot_count / self.cols)

    def index(self, r: int, c: int) -> int:
        return r * self.cols + c

    def is_valid(self, r: int, c: int) -> bool:
        if r < 0 or c < 0 or c >= self.cols or r >= self.rows:
            return False
        return self.index(r, c) < self.slot_count

    def cells(self):
        for i in range(self.slot_count):
            yield divmod(i, self.cols)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_grid.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add sota/model/grid.py tests/test_grid.py
git commit -m "feat: 6-column grid geometry with partial last row"
```

---

## Task 3: Layout container

Holds tablet and artifact placements and answers "what artifact is at `(r,c)`".

**Files:** Create `sota/model/layout.py`; Test `tests/test_layout.py`

- [ ] **Step 1: Write the failing test**

```python
from sota.model.layout import TabletPlacement, ArtifactPlacement, Layout

def test_artifact_lookup_and_iteration():
    lay = Layout(
        slot_count=12,
        tablets=[TabletPlacement(key="peace", row=1, col=1, rotation=0)],
        artifacts=[ArtifactPlacement(key="fire_bolt", row=1, col=0),
                   ArtifactPlacement(key="ohia_lehua", row=1, col=2)],
    )
    assert lay.artifact_at(1, 0).key == "fire_bolt"
    assert lay.artifact_at(0, 0) is None
    assert {a.key for a in lay.artifacts} == {"fire_bolt", "ohia_lehua"}
    assert lay.tablets[0].rotation == 0

def test_rejects_two_items_on_one_cell():
    import pytest
    with pytest.raises(ValueError):
        Layout(slot_count=12,
               tablets=[TabletPlacement(key="peace", row=0, col=0, rotation=0)],
               artifacts=[ArtifactPlacement(key="fire_bolt", row=0, col=0)])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_layout.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement** `sota/model/layout.py`

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class TabletPlacement:
    key: str
    row: int
    col: int
    rotation: int = 0   # 0..3 (90-degree steps)

@dataclass(frozen=True)
class ArtifactPlacement:
    key: str
    row: int
    col: int

@dataclass
class Layout:
    slot_count: int
    tablets: list = field(default_factory=list)
    artifacts: list = field(default_factory=list)

    def __post_init__(self):
        seen = set()
        for p in list(self.tablets) + list(self.artifacts):
            cell = (p.row, p.col)
            if cell in seen:
                raise ValueError(f"two items on cell {cell}")
            seen.add(cell)
        self._art_by_cell = {(a.row, a.col): a for a in self.artifacts}

    def artifact_at(self, row: int, col: int):
        return self._art_by_cell.get((row, col))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_layout.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add sota/model/layout.py tests/test_layout.py
git commit -m "feat: layout container with cell-collision guard"
```

---

## Task 4: Pos-based effects + rotation

`rotate_pos` rotates a `[dx, dy]` offset; `affected_cells` for a pos effect returns the single target cell (in-bounds only).

**Files:** Create `sota/evaluate/__init__.py` (empty), `sota/evaluate/effects.py`; Test `tests/test_effects_pos.py`

- [ ] **Step 1: Write the failing test**

```python
from sota.evaluate.effects import rotate_pos, pos_target
from sota.model.grid import Grid

def test_rotate_pos_90_steps():
    # 90deg CW: (dx,dy) -> (dy,-dx) in up-positive coords
    assert rotate_pos([1, 0], 0) == (1, 0)
    assert rotate_pos([1, 0], 1) == (0, -1)
    assert rotate_pos([1, 0], 2) == (-1, 0)
    assert rotate_pos([1, 0], 3) == (0, 1)
    assert rotate_pos([1, 2], 1) == (2, -1)

def test_pos_target_uses_up_positive_dy():
    g = Grid(36)
    # tablet at (3,3), pos [-1, 2] -> col 3-1=2, row 3-2=1
    assert pos_target(3, 3, [-1, 2], 0, g) == (1, 2)
    # out of bounds returns None
    assert pos_target(0, 0, [0, 1], 0, g) is None   # row 0-1=-1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_effects_pos.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement** (`sota/evaluate/effects.py`, partial — pos only)

```python
def rotate_pos(pos, rotation):
    """Rotate [dx, dy] (dx right+, dy up+) by rotation*90 deg clockwise."""
    dx, dy = pos
    for _ in range(rotation % 4):
        dx, dy = dy, -dx   # 90deg CW in up-positive coords
    return (dx, dy)

def pos_target(trow, tcol, pos, rotation, grid):
    """Cell a pos effect from a tablet at (trow,tcol) targets, or None if off-grid."""
    dx, dy = rotate_pos(pos, rotation)
    r, c = trow - dy, tcol + dx
    return (r, c) if grid.is_valid(r, c) else None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_effects_pos.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add sota/evaluate/__init__.py sota/evaluate/effects.py tests/test_effects_pos.py
git commit -m "feat: pos-effect rotation and targeting (up-positive dy)"
```

---

## Task 5: Shape-based effects

`shape_cells` returns every cell a shape effect (row/column/diagonal/top/bottom) hits. Rotation does NOT apply to shape effects.

**Files:** Modify `sota/evaluate/effects.py`; Test `tests/test_effects_shape.py`

- [ ] **Step 1: Write the failing test**

```python
from sota.evaluate.effects import shape_cells
from sota.model.grid import Grid

G = Grid(36)  # full 6x6

def test_row_and_column():
    assert sorted(shape_cells("row", 2, 3, G)) == [(2, c) for c in range(6)]
    assert sorted(shape_cells("column", 2, 3, G)) == [(r, 3) for r in range(6)]

def test_diagonal_excludes_self():
    cells = set(shape_cells("diagonal", 2, 2, G))
    assert (2, 2) not in cells
    assert (0, 0) in cells and (4, 4) in cells   # main diagonal
    assert (0, 4) in cells and (4, 0) in cells   # anti-diagonal
    assert (2, 3) not in cells                   # not on a diagonal

def test_top_and_bottom_rows():
    assert sorted(shape_cells("top", 3, 1, G)) == [(0, c) for c in range(6)]
    assert sorted(shape_cells("bottom", 3, 1, G)) == [(5, c) for c in range(6)]

def test_partial_grid_excludes_invalid_cells():
    g = Grid(34)  # last row has cols 0..3
    assert (5, 4) not in set(shape_cells("column", 0, 4, g))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_effects_shape.py -v`
Expected: FAIL with `ImportError: cannot import name 'shape_cells'`.

- [ ] **Step 3: Implement** (append to `sota/evaluate/effects.py`)

```python
def shape_cells(shape, trow, tcol, grid):
    """Cells a shape (area) effect from a tablet at (trow,tcol) hits. In-bounds only.

    Provisional semantics (verified against the simulator oracle in Task 8):
      row     -> the tablet's whole row
      column  -> the tablet's whole column
      diagonal-> both diagonals through the tablet (excludes the tablet cell)
      top     -> the topmost row (row 0)
      bottom  -> the bottommost occupied row (grid.rows - 1)
    """
    out = []
    if shape == "row":
        out = [(trow, c) for c in range(grid.cols)]
    elif shape == "column":
        out = [(r, tcol) for r in range(grid.rows)]
    elif shape == "diagonal":
        for r in range(grid.rows):
            for c in range(grid.cols):
                if (r, c) != (trow, tcol) and abs(r - trow) == abs(c - tcol):
                    out.append((r, c))
    elif shape == "top":
        out = [(0, c) for c in range(grid.cols)]
    elif shape == "bottom":
        out = [(grid.rows - 1, c) for c in range(grid.cols)]
    else:
        raise ValueError(f"unknown shape {shape}")
    return [(r, c) for (r, c) in out if grid.is_valid(r, c)]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_effects_shape.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add sota/evaluate/effects.py tests/test_effects_shape.py
git commit -m "feat: shape (area) effect cell resolution"
```

---

## Task 6: Level deltas + effective levels

`level_deltas(layout, grid, gamedata)` sums every `level_add` (pos + shape) onto a per-cell map. `effective_level` clamps. `restriction_remove` is ignored for scoring.

**Files:** Modify `sota/evaluate/effects.py`; Create `sota/evaluate/levels.py`; Test `tests/test_levels.py`

- [ ] **Step 1: Write the failing test**

```python
from sota.model.grid import Grid
from sota.model.layout import Layout, TabletPlacement, ArtifactPlacement
from sota.model.gamedata import load_game_data
from sota.evaluate.effects import level_deltas
from sota.evaluate.levels import effective_level, START_LEVEL

GD = load_game_data()

def test_peace_adds_to_both_horizontal_neighbors():
    g = Grid(12)
    lay = Layout(slot_count=12,
                 tablets=[TabletPlacement("peace", 1, 1, 0)],   # [-1,0]+3, [1,0]+3
                 artifacts=[])
    d = level_deltas(lay, g, GD)
    assert d[(1, 0)] == 3
    assert d[(1, 2)] == 3
    assert (0, 1) not in d

def test_negative_and_stacking():
    g = Grid(12)
    # advent has a [0,-1] level_add -1 (down one). two advents stacking on same cell.
    lay = Layout(slot_count=12,
                 tablets=[TabletPlacement("advent", 0, 0, 0),
                          TabletPlacement("advent", 2, 0, 0)],
                 artifacts=[])
    d = level_deltas(lay, g, GD)
    assert d.get((1, 0)) == -2  # below advent@0 (row1) and below... verify both reach row1

def test_effective_level_clamps_to_max():
    art = {"max_level": 4}
    assert effective_level(art, 0) == START_LEVEL          # start at 1
    assert effective_level(art, 2) == 3
    assert effective_level(art, 99) == 4                   # clamp high
    assert effective_level(art, -99) == 1                  # clamp low
```

Note: in `test_negative_and_stacking`, advent's `[0,-1]` with up-positive dy targets row `trow - (-1) = trow + 1` (one row DOWN). advent@(0,0)→(1,0); advent@(2,0)→(3,0). They do NOT stack on the same cell — so FIX the test to assert `d[(1,0)] == -1` and `d[(3,0)] == -1`. Use this corrected assertion:

```python
    assert d[(1, 0)] == -1
    assert d[(3, 0)] == -1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_levels.py -v`
Expected: FAIL with `ImportError` (level_deltas / effective_level not defined).

- [ ] **Step 3: Implement**

Append to `sota/evaluate/effects.py`:
```python
from collections import defaultdict

def level_deltas(layout, grid, gamedata):
    """Per-cell total level_add delta from all tablets' effects (pos + shape)."""
    deltas = defaultdict(int)
    for tp in layout.tablets:
        tablet = gamedata.tablets.get(tp.key)
        if tablet is None:
            continue
        for eff in tablet["effects"]:
            if eff.get("type") != "level_add":
                continue   # restriction_remove etc. do not change levels
            if "shape" in eff:
                targets = shape_cells(eff["shape"], tp.row, tp.col, grid)
            else:
                t = pos_target(tp.row, tp.col, eff["pos"], tp.rotation, grid)
                targets = [t] if t else []
            for cell in targets:
                deltas[cell] += eff["value"]
    return dict(deltas)
```

Create `sota/evaluate/levels.py`:
```python
START_LEVEL = 1   # provisional; verified in Task 8

def effective_level(artifact, delta):
    """Clamp the artifact's level to [1, max_level] after applying delta."""
    return max(1, min(artifact["max_level"], START_LEVEL + delta))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_levels.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add sota/evaluate/effects.py sota/evaluate/levels.py tests/test_levels.py
git commit -m "feat: per-cell level deltas and clamped effective levels"
```

---

## Task 7: Special-artifact detection + objective score

`is_special` flags artifacts whose effect text indicates global/positional/conditional behavior (approximate handling). `score_layout` computes the objective and a breakdown.

**Files:** Create `sota/evaluate/special.py`, `sota/evaluate/score.py`; Test `tests/test_special.py`, `tests/test_score.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_special.py`:
```python
from sota.model.gamedata import load_game_data
from sota.evaluate.special import is_special

GD = load_game_data()

def test_known_special_flagged():
    assert is_special(GD.artifacts["calges"])        # 위치한 가로줄
    assert is_special(GD.artifacts["black_scales"])  # 인벤토리 내 석판 개수

def test_plain_artifact_not_flagged():
    assert not is_special(GD.artifacts["fire_bolt"])  # [고유] 파이어 볼트 획득
```

`tests/test_score.py`:
```python
from sota.model.grid import Grid
from sota.model.layout import Layout, TabletPlacement, ArtifactPlacement
from sota.model.gamedata import load_game_data
from sota.evaluate.score import score_layout, combo_stages

GD = load_game_data()

def test_combo_stages_counts_thresholds_reached():
    combo = GD.combos["yinggalbul"]          # thresholds 2/4/6/8/10
    assert combo_stages(combo, 0) == 0
    assert combo_stages(combo, 3) == 1       # only >=2 reached
    assert combo_stages(combo, 6) == 3       # 2,4,6
    assert combo_stages(combo, 99) == 5

def test_score_rewards_levels_and_stages():
    g = Grid(12)
    # two yinggalbul artifacts (fire_bolt, ohia_lehua); peace tablet boosts ohia_lehua's cell
    lay = Layout(slot_count=12,
                 tablets=[TabletPlacement("peace", 1, 1, 0)],   # boosts (1,0) and (1,2) by +3
                 artifacts=[ArtifactPlacement("fire_bolt", 1, 0),
                            ArtifactPlacement("ohia_lehua", 1, 2)])
    res = score_layout(lay, "yinggalbul", GD)
    # 2 target artifacts -> 1 stage (>=2). fire_bolt max_level 1 -> level 1.
    # ohia_lehua boosted +3 -> clamped to its max_level.
    assert res.stages == 1
    assert res.level_sum >= 2
    assert res.score == 1000 * res.stages + res.level_sum
    assert res.target_keys == ["fire_bolt", "ohia_lehua"]

def test_non_target_artifacts_ignored_in_level_sum():
    g = Grid(12)
    lay = Layout(slot_count=12, tablets=[],
                 artifacts=[ArtifactPlacement("fire_bolt", 0, 0),       # yinggalbul
                            ArtifactPlacement("blessing", 0, 1)])       # not yinggalbul
    res = score_layout(lay, "yinggalbul", GD)
    assert res.target_keys == ["fire_bolt"]
    assert res.stages == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_special.py tests/test_score.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

`sota/evaluate/special.py`:
```python
# Markers in effect_text indicating global / positional / conditional behavior
# that the v1 level-based model approximates (and flags in the score breakdown).
SPECIAL_MARKERS = (
    "석판", "인벤토리", "가로줄", "세로줄", "위치", "양쪽", "줄에", "개수만큼", "개당",
)

def is_special(artifact) -> bool:
    text = artifact.get("effect_text", "")
    return any(m in text for m in SPECIAL_MARKERS)
```

`sota/evaluate/score.py`:
```python
from dataclasses import dataclass
from sota.model.grid import Grid
from sota.evaluate.effects import level_deltas
from sota.evaluate.levels import effective_level
from sota.evaluate.special import is_special

STAGE_WEIGHT = 1000   # a combo stage dominates level tweaks

@dataclass(frozen=True)
class ScoreResult:
    score: int
    stages: int
    level_sum: int
    target_keys: list
    approximated: list   # special artifacts among the targets (flagged)

def combo_stages(combo, count) -> int:
    return sum(1 for t in combo["thresholds"] if t["count"] <= count)

def score_layout(lay, target_combo, gamedata) -> ScoreResult:
    grid = Grid(lay.slot_count)
    deltas = level_deltas(lay, grid, gamedata)
    target_keys, level_sum, approximated = [], 0, []
    for a in lay.artifacts:
        art = gamedata.artifacts.get(a.key)
        if art is None or target_combo not in art["combos"]:
            continue
        target_keys.append(a.key)
        level_sum += effective_level(art, deltas.get((a.row, a.col), 0))
        if is_special(art):
            approximated.append(a.key)
    combo = gamedata.combos[target_combo]
    stages = combo_stages(combo, len(target_keys))
    score = STAGE_WEIGHT * stages + level_sum
    return ScoreResult(score=score, stages=stages, level_sum=level_sum,
                       target_keys=target_keys, approximated=approximated)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_special.py tests/test_score.py -v`
Expected: PASS (5 passed). If `test_score_rewards_levels_and_stages` fails only on the exact `level_sum` value, adjust the assertion to match the real `ohia_lehua` max_level (read it from data) — keep `>= 2` style assertions, do not change the implementation.

- [ ] **Step 5: Commit**

```bash
git add sota/evaluate/special.py sota/evaluate/score.py tests/test_special.py tests/test_score.py
git commit -m "feat: objective score (combo stages + target level sum) with special flagging"
```

---

## Task 8: Oracle calibration (golden tests)

Verify the provisional mechanics (start level, shape semantics, stacking, clamp) against the wiki simulator, which computes effective levels. Capture a small golden dataset and assert the engine reproduces it. **This task has a manual/browser investigation step — escalate to the controller (who has the simulator tooling) to capture the golden fixtures.**

**Files:** Create `tests/fixtures/golden_layouts.json`; Test `tests/test_oracle_golden.py`

- [ ] **Step 1: Capture golden fixtures from the simulator (controller-assisted)**

Use `https://www.sephiria.wiki/simulator`. For each of these scenarios, place the items, read the simulator's computed effective level for each artifact (it displays them), and record it. Cover the uncertain rules:
1. One artifact alone (no tablet) → confirms **start level** (expect level 1).
2. One artifact + one `peace` tablet adjacent (`[±1,0]+3`) → confirms pos delta + clamp at the artifact's `max_level`.
3. One artifact + a `row`-shape tablet (e.g. `base`/기반, `row +1`) in the same row → confirms **row** semantics.
4. A `column`-shape tablet (`concurrency`/동시성) → confirms **column**.
5. A `diagonal` tablet (`rebellion`/반항) → confirms **diagonal** set.
6. A `top` tablet and a `bottom` tablet → confirms **top/bottom** target rows.
7. A negative tablet (`advent`/도래 `[0,-1]-1`) pointing at an artifact → confirms negatives.

Record each as an entry. Schema (`tests/fixtures/golden_layouts.json`):
```json
[
  {"name": "peace_boosts_neighbor", "slot_count": 12,
   "tablets": [{"key": "peace", "row": 1, "col": 1, "rotation": 0}],
   "artifacts": [{"key": "ohia_lehua", "row": 1, "col": 0}],
   "expected_levels": {"1,0": 4}}
]
```
(`expected_levels` keys are `"row,col"`; the value is the simulator's displayed effective level for the artifact at that cell.)

If a captured value contradicts a provisional rule (start level, a shape definition, the clamp, negatives), FIX the single responsible function in `effects.py`/`levels.py` and note the correction in the commit message — the golden test is the source of truth.

- [ ] **Step 2: Write the golden test** `tests/test_oracle_golden.py`

```python
import json, pathlib
import pytest
from sota.model.gamedata import load_game_data
from sota.model.grid import Grid
from sota.model.layout import Layout, TabletPlacement, ArtifactPlacement
from sota.evaluate.effects import level_deltas
from sota.evaluate.levels import effective_level

GD = load_game_data()
FIX = pathlib.Path(__file__).parent / "fixtures" / "golden_layouts.json"

def _cases():
    if not FIX.exists():
        return []
    return json.loads(FIX.read_text(encoding="utf-8"))

@pytest.mark.parametrize("case", _cases(), ids=lambda c: c["name"])
def test_engine_matches_simulator(case):
    lay = Layout(slot_count=case["slot_count"],
                 tablets=[TabletPlacement(**t) for t in case["tablets"]],
                 artifacts=[ArtifactPlacement(**a) for a in case["artifacts"]])
    grid = Grid(lay.slot_count)
    deltas = level_deltas(lay, grid, GD)
    for cell_str, expected in case["expected_levels"].items():
        r, c = map(int, cell_str.split(","))
        art = GD.artifacts[lay.artifact_at(r, c).key]
        assert effective_level(art, deltas.get((r, c), 0)) == expected, \
            f"{case['name']} @ {cell_str}: got {effective_level(art, deltas.get((r,c),0))}, exp {expected}"
```

- [ ] **Step 3: Run the golden test**

Run: `python3 -m pytest tests/test_oracle_golden.py -v`
Expected: PASS for every captured case (the suite is parametrized; with no fixtures it collects 0 — fixtures MUST be captured in Step 1 for this task to be meaningful).

- [ ] **Step 4: Run the full suite**

Run: `python3 -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/golden_layouts.json tests/test_oracle_golden.py sota/evaluate/effects.py sota/evaluate/levels.py
git commit -m "test: oracle golden fixtures; calibrate mechanics to simulator"
```

---

## Self-Review Notes (addressed)

- **Spec coverage:** §2 grid (T2) + pos/shape effects + up-positive dy + rotation (T4,T5) + level clamp (T6) + restriction_remove no-op (T6); §3 objective = stages + level sum (T7); §4 special-artifact approximate-and-flag (T7); §12 oracle golden tests (T8). Shape effects (the mechanic discovered in sub-plan 1) are first-class (T5).
- **Provisional rules are isolated** in `effects.shape_cells`, `effects.level_deltas`, and `levels.py` so T8 can correct them in one place without touching the score logic.
- **Type consistency:** `Layout`/`TabletPlacement`/`ArtifactPlacement` defined in T3 and used identically in T6–T8; `level_deltas(layout, grid, gamedata)` signature stable T6→T8; `ScoreResult` fields (`score, stages, level_sum, target_keys, approximated`) defined T7.
- **Known approximations (documented, not silent):** special artifacts scored by level only and listed in `ScoreResult.approximated`; `restriction_remove` ignored for scoring (it constrains placement legality, handled by the sub-plan 3 solver, not the score); `START_LEVEL`/shape semantics provisional until T8 golden capture.
- **Out of scope (sub-plan 3+):** placement legality/restrictions, the GA search, recognition, rendering. The engine is a pure fitness function over a given legal layout.
