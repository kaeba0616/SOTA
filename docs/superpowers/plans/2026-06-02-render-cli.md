# Render + CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the optimizer runnable: one command takes the items you own (tablet + artifact keys), a target combo, and a slot count, runs the GA solver, prints a readable build summary, and writes an arranged-grid PNG of the optimal layout.

**Architecture:** A pure structured-summary builder (score, stages, per-artifact effective level, placements, approximations) drives both the text output and the image. A Pillow renderer draws the 6-column grid with item icons (from `assets/`) and effective-level badges. A thin CLI wires argument parsing + key validation → `solve` → summary + image. Pure logic is TDD'd; the Pillow rendering is smoke-tested (dimensions + file written).

**Tech Stack:** Python 3.12, pytest, Pillow. Reads `sota/data/*.json` and `assets/{tablets,artifacts}/`.

**This is sub-project 5 of 5.** Depends on sub-plans 1–3 (`sota/model`, `sota/evaluate`, `sota/solve.solve`, `sota/data/idmap.json`, synced `assets/`). Independent of sub-plan 4 (recognition) — the CLI takes item keys directly, so the tool is fully usable now; sub-plan 4 later auto-fills those keys from a screenshot. See `docs/superpowers/specs/2026-06-01-combo-build-optimizer-design.md` §9.

---

## Key facts / decisions

- Artifact image filename ≠ key in general → resolve via `sota/data/idmap.json` (`map[key] -> filename-without-ext`), then glob for the real extension (`.png`/`.webp`). Tablet image = `assets/tablets/{key}.png` (all synced).
- Effective level for display reuses `evaluate.effects.level_deltas` + `evaluate.levels.effective_level` (provisional start-level/clamp per `docs/CALIBRATION.md`).
- The summary is the single source of truth the renderer and the text output both consume.
- The CLI validates every item/combo key up front and fails with a helpful message (no silent typos).

---

## File Structure

```
sota/
  render/
    __init__.py
    summary.py       # build_summary(layout, target_combo, gamedata) -> dict; format_summary(dict) -> str
    icons.py         # icon_path(kind, key, root) -> Path | None
    grid_image.py    # render_layout(layout, target_combo, gamedata, root, cell=64) -> PIL.Image
  cli.py             # run(...) -> summary dict (+ writes image); main(argv) argparse entrypoint
tests/
  test_summary.py
  test_icons.py
  test_grid_image.py
  test_cli.py
```

---

## Task 1: Structured build summary (pure)

**Files:** Create `sota/render/__init__.py` (empty), `sota/render/summary.py`; Test `tests/test_summary.py`

- [ ] **Step 1: Write the failing test**

```python
from sota.model.grid import Grid
from sota.model.layout import Layout, TabletPlacement, ArtifactPlacement
from sota.model.gamedata import load_game_data
from sota.render.summary import build_summary, format_summary

GD = load_game_data()

def test_build_summary_fields():
    lay = Layout(slot_count=12,
                 tablets=[TabletPlacement("peace", 0, 1, 0)],
                 artifacts=[ArtifactPlacement("fire_bolt", 0, 0),
                            ArtifactPlacement("ohia_lehua", 0, 2)])
    s = build_summary(lay, "yinggalbul", GD)
    assert s["stages"] == 1
    assert s["score"] == 1000 * s["stages"] + s["level_sum"]
    # ohia_lehua boosted by peace (+3) -> clamped to its max_level 3
    ohia = next(t for t in s["targets"] if t["key"] == "ohia_lehua")
    assert ohia["cell"] == [0, 2] and ohia["level"] == 3
    fire = next(t for t in s["targets"] if t["key"] == "fire_bolt")
    assert fire["level"] == 1                     # max_level 1
    assert {t["key"] for t in s["tablets"]} == {"peace"}
    assert s["approximated"] == []

def test_format_summary_is_readable_text():
    lay = Layout(slot_count=12, tablets=[],
                 artifacts=[ArtifactPlacement("fire_bolt", 0, 0)])
    txt = format_summary(build_summary(lay, "yinggalbul", GD))
    assert "yinggalbul" in txt
    assert "fire_bolt" in txt
    assert "score" in txt.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_summary.py -v`
Expected: FAIL `ModuleNotFoundError`.

- [ ] **Step 3: Implement** `sota/render/summary.py`

```python
from sota.model.grid import Grid
from sota.evaluate.effects import level_deltas
from sota.evaluate.levels import effective_level
from sota.evaluate.score import score_layout

def build_summary(layout, target_combo, gamedata) -> dict:
    grid = Grid(layout.slot_count)
    deltas = level_deltas(layout, grid, gamedata)
    res = score_layout(layout, target_combo, gamedata)
    targets = []
    for a in layout.artifacts:
        art = gamedata.artifacts.get(a.key)
        if art is None or target_combo not in art["combos"]:
            continue
        targets.append({
            "key": a.key,
            "name": art["name_kor"],
            "cell": [a.row, a.col],
            "level": effective_level(art, deltas.get((a.row, a.col), 0)),
            "max_level": art["max_level"],
            "special": a.key in res.approximated,
        })
    return {
        "combo": target_combo,
        "score": res.score,
        "stages": res.stages,
        "level_sum": res.level_sum,
        "targets": targets,
        "tablets": [{"key": t.key, "cell": [t.row, t.col], "rotation": t.rotation}
                    for t in layout.tablets],
        "approximated": list(res.approximated),
    }

def format_summary(s: dict) -> str:
    lines = [
        f"combo: {s['combo']}",
        f"score: {s['score']}  (stages {s['stages']} x 1000 + levels {s['level_sum']})",
        f"target artifacts ({len(s['targets'])}):",
    ]
    for t in s["targets"]:
        mark = " *approx" if t["special"] else ""
        lines.append(f"  - {t['key']} @ {t['cell']}  Lv {t['level']}/{t['max_level']}{mark}")
    lines.append(f"tablets ({len(s['tablets'])}): " + ", ".join(
        f"{t['key']}@{t['cell']}" for t in s["tablets"]))
    if s["approximated"]:
        lines.append("approximated (special, level-only): " + ", ".join(s["approximated"]))
    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_summary.py -v`
Expected: PASS (2 passed). If `ohia_lehua`'s level isn't 3, read its real `max_level` from data and adjust the assertion to the true clamped value — do not change the implementation.

- [ ] **Step 5: Commit**

```bash
git add sota/render/__init__.py sota/render/summary.py tests/test_summary.py
git commit -m "feat: structured build summary + text formatter"
```

---

## Task 2: Icon path resolver

**Files:** Create `sota/render/icons.py`; Test `tests/test_icons.py`

- [ ] **Step 1: Write the failing test**

```python
import pathlib
from sota.render.icons import icon_path

ROOT = pathlib.Path(__file__).resolve().parents[1]   # SOTA/

def test_tablet_icon_resolves():
    p = icon_path("tablet", "peace", ROOT)
    assert p is not None and p.exists() and p.name == "peace.png"

def test_artifact_icon_resolves_via_idmap():
    # fire_bolt maps to a real file (png or webp)
    p = icon_path("artifact", "fire_bolt", ROOT)
    assert p is not None and p.exists()

def test_unknown_key_returns_none():
    assert icon_path("artifact", "definitely_not_real", ROOT) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_icons.py -v`
Expected: FAIL `ModuleNotFoundError`.

- [ ] **Step 3: Implement** `sota/render/icons.py`

```python
import json, functools, pathlib

@functools.lru_cache(maxsize=8)
def _idmap(root_str):
    p = pathlib.Path(root_str) / "sota" / "data" / "idmap.json"
    return json.loads(p.read_text(encoding="utf-8"))["map"]

def icon_path(kind, key, root):
    """Absolute path to an item's image, or None. Artifacts resolve through idmap
    (key -> filename) then glob the real extension; tablets are assets/tablets/{key}.png."""
    root = pathlib.Path(root)
    if kind == "tablet":
        p = root / "assets" / "tablets" / f"{key}.png"
        return p if p.exists() else None
    filename = _idmap(str(root)).get(key)
    if filename is None:
        return None
    matches = sorted((root / "assets" / "artifacts").glob(f"{filename}.*"))
    return matches[0] if matches else None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_icons.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add sota/render/icons.py tests/test_icons.py
git commit -m "feat: item icon path resolver (idmap-aware)"
```

---

## Task 3: Grid image renderer (Pillow)

**Files:** Modify `pyproject.toml` (add Pillow); Create `sota/render/grid_image.py`; Test `tests/test_grid_image.py`

- [ ] **Step 1: Add Pillow and install**

In `pyproject.toml`, add `"pillow>=10.0"` to `[project].dependencies`. Then:
```bash
pip install pillow --break-system-packages 2>/dev/null || pip install pillow
python3 -c "import PIL; print('pillow', PIL.__version__)"
```
Expected: prints a pillow version.

- [ ] **Step 2: Write the failing test**

```python
import pathlib
from PIL import Image
from sota.model.layout import Layout, TabletPlacement, ArtifactPlacement
from sota.model.gamedata import load_game_data
from sota.render.grid_image import render_layout

GD = load_game_data()
ROOT = pathlib.Path(__file__).resolve().parents[1]

def test_render_returns_image_of_expected_size():
    lay = Layout(slot_count=12,
                 tablets=[TabletPlacement("peace", 0, 1, 0)],
                 artifacts=[ArtifactPlacement("fire_bolt", 0, 0),
                            ArtifactPlacement("ohia_lehua", 0, 2)])
    img = render_layout(lay, "yinggalbul", GD, ROOT, cell=48)
    assert isinstance(img, Image.Image)
    assert img.width == 6 * 48                    # 6 columns
    assert img.height >= 2 * 48                   # >=2 grid rows (12 slots) + header
    assert img.mode in ("RGB", "RGBA")

def test_render_saves_nonempty_png(tmp_path):
    lay = Layout(slot_count=6, tablets=[], artifacts=[ArtifactPlacement("fire_bolt", 0, 0)])
    img = render_layout(lay, "yinggalbul", GD, ROOT, cell=48)
    out = tmp_path / "layout.png"
    img.save(out)
    assert out.exists() and out.stat().st_size > 100
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python3 -m pytest tests/test_grid_image.py -v`
Expected: FAIL `ModuleNotFoundError`.

- [ ] **Step 4: Implement** `sota/render/grid_image.py`

```python
from PIL import Image, ImageDraw
from sota.model.grid import Grid
from sota.evaluate.effects import level_deltas
from sota.evaluate.levels import effective_level
from sota.render.icons import icon_path

_BG = (40, 30, 45)
_CELL = (70, 50, 60)
_LINE = (90, 70, 80)
_HEADER_H = 28

def render_layout(layout, target_combo, gamedata, root, cell=64):
    grid = Grid(layout.slot_count)
    w = grid.cols * cell
    h = _HEADER_H + grid.rows * cell
    img = Image.new("RGB", (w, h), _BG)
    d = ImageDraw.Draw(img)
    d.text((6, 8), f"{target_combo}", fill=(230, 220, 225))

    # empty cells
    for (r, c) in grid.cells():
        x0, y0 = c * cell, _HEADER_H + r * cell
        d.rectangle([x0, y0, x0 + cell - 1, y0 + cell - 1], fill=_CELL, outline=_LINE)

    deltas = level_deltas(layout, grid, gamedata)

    def paste_icon(kind, key, r, c):
        p = icon_path(kind, key, root)
        x0, y0 = c * cell, _HEADER_H + r * cell
        if p is not None:
            ico = Image.open(p).convert("RGBA").resize((cell - 6, cell - 6))
            img.paste(ico, (x0 + 3, y0 + 3), ico)
        else:
            d.text((x0 + 4, y0 + 4), key[:6], fill=(220, 220, 220))

    for t in layout.tablets:
        paste_icon("tablet", t.key, t.row, t.col)
    for a in layout.artifacts:
        paste_icon("artifact", a.key, a.row, a.col)
        art = gamedata.artifacts.get(a.key)
        if art is not None:
            lvl = effective_level(art, deltas.get((a.row, a.col), 0))
            x0, y0 = a.col * cell, _HEADER_H + a.row * cell
            d.text((x0 + 3, y0 + cell - 14), f"L{lvl}", fill=(255, 235, 120))
    return img
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 -m pytest tests/test_grid_image.py -v`
Expected: PASS (2 passed).

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml sota/render/grid_image.py tests/test_grid_image.py
git commit -m "feat: Pillow grid-layout renderer with level badges"
```

---

## Task 4: CLI core (`run`)

A pure-ish function that takes raw keys, validates them, solves, builds the summary, and writes the image. Returns the summary dict.

**Files:** Create `sota/cli.py`; Test `tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

```python
import pathlib
from sota.model.gamedata import load_game_data
from sota.cli import run

GD = load_game_data()
ROOT = pathlib.Path(__file__).resolve().parents[1]

def test_run_solves_and_writes_image(tmp_path):
    out = tmp_path / "build.png"
    summary = run(tablets=["peace"], artifacts=["fire_bolt", "ohia_lehua"],
                  combo="yinggalbul", slots=12, seed=7, out=str(out),
                  gamedata=GD, root=ROOT, generations=20, pop_size=24)
    assert summary["combo"] == "yinggalbul"
    assert summary["score"] >= 1000
    assert out.exists() and out.stat().st_size > 100

def test_run_rejects_unknown_keys():
    import pytest
    with pytest.raises(ValueError) as e:
        run(tablets=["nope_tablet"], artifacts=[], combo="yinggalbul",
            slots=12, seed=0, out=None, gamedata=GD, root=ROOT)
    assert "nope_tablet" in str(e.value)

def test_run_rejects_unknown_combo():
    import pytest
    with pytest.raises(ValueError) as e:
        run(tablets=[], artifacts=["fire_bolt"], combo="not_a_combo",
            slots=12, seed=0, out=None, gamedata=GD, root=ROOT)
    assert "not_a_combo" in str(e.value)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_cli.py -v`
Expected: FAIL `ModuleNotFoundError`.

- [ ] **Step 3: Implement** `sota/cli.py` (the `run` function; `main` added in Task 5)

```python
from sota.model.pool import ItemPool
from sota.solve.ga import solve
from sota.render.summary import build_summary
from sota.render.grid_image import render_layout

def _validate(keys, valid, label):
    bad = [k for k in keys if k not in valid]
    if bad:
        raise ValueError(f"unknown {label}: {bad}")

def run(*, tablets, artifacts, combo, slots, seed, out, gamedata, root,
        generations=60, pop_size=40):
    _validate(tablets, gamedata.tablets, "tablet key")
    _validate(artifacts, gamedata.artifacts, "artifact key")
    if combo not in gamedata.combos:
        raise ValueError(f"unknown combo: {combo}")
    pool = ItemPool(tablets=list(tablets), artifacts=list(artifacts))
    result = solve(pool, combo, slot_count=slots, gamedata=gamedata,
                   seed=seed, generations=generations, pop_size=pop_size)
    summary = build_summary(result.layout, combo, gamedata)
    if out is not None:
        render_layout(result.layout, combo, gamedata, root).save(out)
    return summary
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_cli.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add sota/cli.py tests/test_cli.py
git commit -m "feat: CLI core run() (validate, solve, summarize, render)"
```

---

## Task 5: CLI entrypoint + argparse + README

**Files:** Modify `sota/cli.py` (add `main`); Modify `README.md`

- [ ] **Step 1: Add `main(argv)` to `sota/cli.py`**

```python
import argparse, pathlib, sys
from sota.model.gamedata import load_game_data
from sota.render.summary import format_summary

def main(argv=None):
    ap = argparse.ArgumentParser(prog="sota", description="Sephiria combo-build optimizer")
    ap.add_argument("--combo", help="target combo key (e.g. yinggalbul)")
    ap.add_argument("--tablets", default="", help="comma-separated tablet keys")
    ap.add_argument("--artifacts", default="", help="comma-separated artifact keys")
    ap.add_argument("--slots", type=int, default=34, help="inventory slot count")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--generations", type=int, default=60)
    ap.add_argument("--pop-size", type=int, default=40)
    ap.add_argument("--out", default="build.png", help="output image path")
    ap.add_argument("--list-combos", action="store_true", help="list combo keys and exit")
    args = ap.parse_args(argv)

    gd = load_game_data()
    if args.list_combos:
        for k, c in gd.combos.items():
            print(f"{k:18s} {c['label']}")
        return 0
    if not args.combo:
        ap.error("--combo is required (or use --list-combos)")

    def split(s):
        return [x.strip() for x in s.split(",") if x.strip()]

    root = pathlib.Path(__file__).resolve().parents[1]
    try:
        summary = run(tablets=split(args.tablets), artifacts=split(args.artifacts),
                      combo=args.combo, slots=args.slots, seed=args.seed, out=args.out,
                      gamedata=gd, root=root,
                      generations=args.generations, pop_size=args.pop_size)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(format_summary(summary))
    print(f"\nimage written to {args.out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Manual smoke run**

```bash
python3 -m sota.cli --list-combos
python3 -m sota.cli --combo yinggalbul --tablets peace,honor --artifacts fire_bolt,ohia_lehua,ignition --slots 16 --seed 1 --out /tmp/sota_build.png
```
Expected: `--list-combos` prints 19 combos; the second prints a summary (score, target artifacts with levels, tablets) and `image written to /tmp/sota_build.png`. Confirm the file exists: `test -s /tmp/sota_build.png && echo OK`.

- [ ] **Step 3: Update `README.md`**

Replace the stub README body with a short usage section:
```markdown
# SOTA (Sephiria Optimal Tablet Arranger)
세피리아 석판 최적화 배치 자동 계산기

## Usage
```
python3 -m sota.cli --list-combos
python3 -m sota.cli --combo yinggalbul \
    --tablets peace,honor,courage \
    --artifacts fire_bolt,ohia_lehua,ignition,magma_bead \
    --slots 34 --seed 1 --out build.png
```
Outputs a build summary (score = combo stages x1000 + target level sum) and an
arranged-grid PNG. Item keys are the English keys in `sota/data/{tablets,artifacts}.json`.

## Pipeline
data (`sota/data`) -> evaluation engine (`sota/evaluate`) -> GA solver (`sota/solve`) -> render/CLI (`sota/render`, `sota/cli.py`).
See `docs/superpowers/` for specs and plans, `docs/CALIBRATION.md` for known approximations.
```

- [ ] **Step 4: Commit**

```bash
git add sota/cli.py README.md
git commit -m "feat: sota CLI entrypoint (argparse, list-combos) + README usage"
```

---

## Task 6: End-to-end CLI test + full suite gate

**Files:** Modify `tests/test_cli.py`

- [ ] **Step 1: Add an end-to-end test invoking `main`**

```python
def test_main_list_combos(capsys):
    from sota.cli import main
    rc = main(["--list-combos"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "yinggalbul" in out
    assert len(out.strip().splitlines()) == 19

def test_main_full_run(tmp_path, capsys):
    from sota.cli import main
    out = tmp_path / "b.png"
    rc = main(["--combo", "yinggalbul", "--tablets", "peace",
               "--artifacts", "fire_bolt,ohia_lehua", "--slots", "12",
               "--seed", "5", "--generations", "15", "--pop-size", "20",
               "--out", str(out)])
    assert rc == 0
    assert out.exists() and out.stat().st_size > 100
    assert "score" in capsys.readouterr().out.lower()

def test_main_unknown_combo_returns_error_code(capsys):
    from sota.cli import main
    rc = main(["--combo", "bogus", "--artifacts", "fire_bolt"])
    assert rc == 2
    assert "bogus" in capsys.readouterr().err
```

- [ ] **Step 2: Run the CLI tests**

Run: `python3 -m pytest tests/test_cli.py -v`
Expected: PASS (6 passed total).

- [ ] **Step 3: Full suite**

Run: `python3 -m pytest -q`
Expected: all pass (report the count).

- [ ] **Step 4: Commit**

```bash
git add tests/test_cli.py
git commit -m "test: end-to-end CLI (list-combos, full run, error code)"
```

---

## Self-Review Notes (addressed)

- **Spec coverage (§9):** structured summary with per-artifact effective levels + combo stages (T1); icon resolution honoring the idmap drift (T2); grid PNG with icons + level badges (T3); one-command CLI: keys + combo + slots -> summary + image (T4,T5); `--list-combos` discovery; up-front key/combo validation with helpful errors (T4,T5); README usage (T5); end-to-end test (T6).
- **Type consistency:** `build_summary(...) -> dict` shape (`combo, score, stages, level_sum, targets[], tablets[], approximated[]`) defined T1 and consumed by `format_summary` (T1), `render_layout` reuse of `level_deltas`/`effective_level` (T3), and `run` (T4); `icon_path(kind, key, root)` signature stable T2->T3; `run(*, tablets, artifacts, combo, slots, seed, out, gamedata, root, ...)` stable T4->T5.
- **Testing posture:** pure summary/icons/CLI-core are asserted on content; Pillow rendering is smoke-tested (size + non-empty file) since pixel-exact assertions are brittle.
- **Known approximations surfaced, not hidden:** effective levels use the provisional start-level/clamp (docs/CALIBRATION.md); special artifacts are marked `*approx` in `format_summary` and listed in the summary's `approximated`.
- **Out of scope (sub-plan 4):** building the item lists from a screenshot — the CLI takes keys directly so the tool ships now; recognition later just fills `--tablets/--artifacts` automatically.
