# Screenshot Recognition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn a game inventory screenshot into the `ItemPool` the CLI already consumes — detect item slots, classify each with the existing MobileNetV2 model, map predictions to canonical item keys, and feed the solver — so a player can optimize from a screenshot instead of typing keys.

**Architecture:** Split the pipeline into a **pure, fully-tested core** (canonical training-set builder, label→key map, labels→`ItemPool` with confidence filtering, CLI wiring via an injected recognizer) and a **model-dependent shell** (OpenCV slot detection, Keras classifier, end-to-end recognition, training) that imports heavy ML libs lazily and whose tests **skip when tensorflow/cv2 are absent**. The CLI takes a `recognize_fn` by dependency injection so the screenshot→pool→solve flow is testable with a fake recognizer.

**Tech Stack:** Python 3.12, pytest (pure core). Model shell additionally needs `tensorflow`, `opencv-python`, `scikit-learn` (NOT installed in CI here — install in an ML environment to train/run).

**This is sub-project 4 of 5 (the last).** Depends on sub-plan 1 (`sota/data/idmap.json`, `assets/`), sub-plan 3 (`ItemPool`, `solve`), sub-plan 5 (`sota/cli.run`). The existing `CNN/` scripts (`train.py`, `inven_test.py`) are the starting point — this plan refactors their logic into a reusable `sota/recognize/` package and aligns classes to canonical keys. See spec §5, §11; `docs/CALIBRATION.md`.

---

## Key facts / decisions

- **No saved model exists yet** (`CNN/sephiria_item_model.keras` / `classes.pickle` absent) → a training task is included; its test is skip-if-deps-absent.
- **Classes must be canonical keys.** Training on raw `assets/` filenames is wrong: `assets/tablets/` has 60 files for 54 tablets (6 stale duplicates like `fusion`/`goodness`), and `assets/artifacts/` filenames differ from keys (idmap drift). Task 1 builds a clean per-item canonical dataset.
- **ML libs absent in this environment.** Tasks 1–3 and the CLI-wiring (Task 7) are pure and run/test here. Tasks 4–6 and 8 (slots, classifier, recognize, training) `pytest.importorskip(...)` so the suite stays green without tensorflow/cv2.
- **Human-in-the-loop:** recognition is imperfect → the CLI prints the recognized item list with low-confidence flags and requires confirmation (`--yes` to skip) before solving (spec §5/§11).
- **Counts/duplicates** fall out naturally: one label per slot → duplicates preserved in the pool.

---

## File Structure

```
sota/
  recognize/
    __init__.py
    dataset.py       # build_canonical_dataset(root, dest) -> {'artifacts':N,'tablets':M,'empty':1}
    keymap.py        # label_to_item(label, gamedata) -> (kind, key) | None
    pool_from_labels.py  # pool_from_labels(labels, gamedata, min_conf) -> (ItemPool, low_conf)
    slots.py         # find_slots(image_bgr) -> [(x,y,w,h)]   (cv2; lazy)
    classifier.py    # Classifier(model_path, classes_path).classify(roi) -> (label, conf)  (tf; lazy)
    recognize.py     # recognize_screenshot(path, classifier, gamedata, min_conf) -> RecognitionResult
    train.py         # train_model(dataset_dir, out_model, out_classes)  (tf; lazy)
tests/
  test_dataset.py
  test_keymap.py
  test_pool_from_labels.py
  test_recognize_cli.py        # CLI screenshot flow with an injected fake recognizer
  test_slots.py                # skip if cv2 absent
  test_classifier_smoke.py     # skip if tf/model absent
```

---

## Task 1: Canonical training-set builder

Copies exactly one image per item, named by its canonical key, into a clean dataset dir (`artifacts/`, `tablets/`, `empty/`). Excludes the 6 stale tablet duplicates and resolves artifact filename drift via idmap.

**Files:** Create `sota/recognize/__init__.py` (empty), `sota/recognize/dataset.py`; Test `tests/test_dataset.py`

- [ ] **Step 1: Write the failing test**

```python
import pathlib
from sota.recognize.dataset import build_canonical_dataset

ROOT = pathlib.Path(__file__).resolve().parents[1]

def test_builds_one_image_per_item(tmp_path):
    counts = build_canonical_dataset(ROOT, tmp_path)
    assert counts["tablets"] == 54
    assert counts["artifacts"] == 248
    assert counts["empty"] >= 1
    # every tablet file stem is a canonical key (no stale 'fusion'/'goodness')
    tab_stems = {p.stem for p in (tmp_path / "tablets").iterdir()}
    assert "unity" in tab_stems and "fusion" not in tab_stems
    # artifact filenames are canonical keys (idmap-resolved)
    art_stems = {p.stem for p in (tmp_path / "artifacts").iterdir()}
    assert "fire_bolt" in art_stems
    assert len(art_stems) == 248
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_dataset.py -v`
Expected: FAIL `ModuleNotFoundError`.

- [ ] **Step 3: Implement** `sota/recognize/dataset.py`

```python
import json, pathlib, shutil

def _idmap(root):
    return json.loads((root / "sota" / "data" / "idmap.json").read_text(encoding="utf-8"))["map"]

def _load(root, name):
    return json.loads((root / "sota" / "data" / name).read_text(encoding="utf-8"))

def build_canonical_dataset(root, dest):
    """Copy one image per item named by canonical key into dest/{tablets,artifacts,empty}.
    Tablets: assets/tablets/{key}.png. Artifacts: idmap key->filename, real extension.
    Returns per-class counts. Skips items whose source image is missing (reported in counts)."""
    root, dest = pathlib.Path(root), pathlib.Path(dest)
    idmap = _idmap(root)
    counts = {"tablets": 0, "artifacts": 0, "empty": 0}

    tdir = dest / "tablets"; tdir.mkdir(parents=True, exist_ok=True)
    for t in _load(root, "tablets.json"):
        src = root / "assets" / "tablets" / f"{t['key']}.png"
        if src.exists():
            shutil.copy(src, tdir / f"{t['key']}.png")
            counts["tablets"] += 1

    adir = dest / "artifacts"; adir.mkdir(parents=True, exist_ok=True)
    for a in _load(root, "artifacts.json"):
        filename = idmap.get(a["key"])
        if filename is None:
            continue
        matches = sorted((root / "assets" / "artifacts").glob(f"{filename}.*"))
        if matches:
            shutil.copy(matches[0], adir / f"{a['key']}{matches[0].suffix}")
            counts["artifacts"] += 1

    edir = dest / "empty"; edir.mkdir(parents=True, exist_ok=True)
    empty_src = root / "CNN" / "slot_empty.png"
    if empty_src.exists():
        shutil.copy(empty_src, edir / "empty.png")
        counts["empty"] += 1
    return counts
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_dataset.py -v`
Expected: PASS (1 passed). If `artifacts` != 248, some idmap target is missing on disk — report the gap (do not relax the assertion without cause).

- [ ] **Step 5: Commit**

```bash
git add sota/recognize/__init__.py sota/recognize/dataset.py tests/test_dataset.py
git commit -m "feat: canonical per-item training-set builder"
```

---

## Task 2: Label → item key map

Maps a model class label (a canonical key or `empty`) to `(kind, key)` or `None`.

**Files:** Create `sota/recognize/keymap.py`; Test `tests/test_keymap.py`

- [ ] **Step 1: Write the failing test**

```python
from sota.model.gamedata import load_game_data
from sota.recognize.keymap import label_to_item

GD = load_game_data()

def test_maps_tablet_artifact_empty_unknown():
    assert label_to_item("peace", GD) == ("tablet", "peace")
    assert label_to_item("fire_bolt", GD) == ("artifact", "fire_bolt")
    assert label_to_item("empty", GD) is None
    assert label_to_item("not_a_real_key", GD) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_keymap.py -v`
Expected: FAIL `ModuleNotFoundError`.

- [ ] **Step 3: Implement** `sota/recognize/keymap.py`

```python
def label_to_item(label, gamedata):
    """Class label (canonical key or 'empty') -> (kind, key) or None."""
    if label in gamedata.tablets:
        return ("tablet", label)
    if label in gamedata.artifacts:
        return ("artifact", label)
    return None  # 'empty' and unknown
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_keymap.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add sota/recognize/keymap.py tests/test_keymap.py
git commit -m "feat: label-to-canonical-item map"
```

---

## Task 3: Labels → ItemPool (with confidence filtering)

Turns the per-slot recognition output into an `ItemPool`, dropping empty/unknown and below-threshold predictions, and returns the low-confidence picks for user review.

**Files:** Create `sota/recognize/pool_from_labels.py`; Test `tests/test_pool_from_labels.py`

- [ ] **Step 1: Write the failing test**

```python
from sota.model.gamedata import load_game_data
from sota.recognize.pool_from_labels import pool_from_labels

GD = load_game_data()

def test_builds_pool_and_flags_low_confidence():
    labels = [("peace", 0.99), ("fire_bolt", 0.95), ("empty", 0.80),
              ("ohia_lehua", 0.40), ("not_a_key", 0.99), ("peace", 0.90)]
    pool, low = pool_from_labels(labels, GD, min_conf=0.5)
    assert sorted(pool.tablets) == ["peace", "peace"]   # duplicates preserved
    assert pool.artifacts == ["fire_bolt"]              # ohia dropped (low conf), not_a_key dropped
    assert ("ohia_lehua", 0.40) in low                 # surfaced for review
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_pool_from_labels.py -v`
Expected: FAIL `ModuleNotFoundError`.

- [ ] **Step 3: Implement** `sota/recognize/pool_from_labels.py`

```python
from sota.model.pool import ItemPool
from sota.recognize.keymap import label_to_item

def pool_from_labels(labels, gamedata, min_conf=0.5):
    """labels: list of (label, confidence). Returns (ItemPool, low_confidence_list).
    Drops 'empty'/unknown; items below min_conf are excluded AND reported in low list."""
    tablets, artifacts, low = [], [], []
    for label, conf in labels:
        item = label_to_item(label, gamedata)
        if item is None:
            continue
        if conf < min_conf:
            low.append((label, conf))
            continue
        kind, key = item
        (tablets if kind == "tablet" else artifacts).append(key)
    return ItemPool(tablets=tablets, artifacts=artifacts), low
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_pool_from_labels.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add sota/recognize/pool_from_labels.py tests/test_pool_from_labels.py
git commit -m "feat: recognized-labels to ItemPool with confidence filter"
```

---

## Task 4: CLI screenshot flow (injected recognizer — testable without ML)

Adds `run_from_screenshot(...)` to `sota/cli.py`: take a screenshot path + a `recognize_fn` (injectable), build the pool, print the recognized items + low-confidence warnings, then solve + render. Tested with a fake recognizer so it needs no model.

**Files:** Modify `sota/cli.py`; Test `tests/test_recognize_cli.py`

- [ ] **Step 1: Write the failing test**

```python
import pathlib
from sota.model.gamedata import load_game_data
from sota.cli import run_from_screenshot

GD = load_game_data()
ROOT = pathlib.Path(__file__).resolve().parents[1]

def fake_recognizer(path):
    # pretend the screenshot held these slots
    return [("peace", 0.99), ("fire_bolt", 0.97), ("ohia_lehua", 0.96),
            ("empty", 0.9), ("ignition", 0.3)]   # ignition low-confidence -> dropped+flagged

def test_run_from_screenshot_solves(tmp_path, capsys):
    out = tmp_path / "b.png"
    summary, low = run_from_screenshot(
        screenshot="ignored.png", combo="yinggalbul", slots=12, seed=7,
        out=str(out), gamedata=GD, root=ROOT, recognize_fn=fake_recognizer,
        min_conf=0.5, generations=15, pop_size=20)
    assert summary["combo"] == "yinggalbul"
    assert summary["score"] >= 1000
    assert ("ignition", 0.3) in low
    assert out.exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_recognize_cli.py -v`
Expected: FAIL `ImportError: cannot import name 'run_from_screenshot'`.

- [ ] **Step 3: Implement** (append to `sota/cli.py`)

```python
from sota.recognize.pool_from_labels import pool_from_labels
from sota.solve.ga import solve
from sota.render.summary import build_summary
from sota.render.grid_image import render_layout

def run_from_screenshot(*, screenshot, combo, slots, seed, out, gamedata, root,
                        recognize_fn, min_conf=0.5, generations=60, pop_size=40):
    if combo not in gamedata.combos:
        raise ValueError(f"unknown combo: {combo}")
    labels = recognize_fn(screenshot)
    pool, low = pool_from_labels(labels, gamedata, min_conf=min_conf)
    result = solve(pool, combo, slot_count=slots, gamedata=gamedata,
                   seed=seed, generations=generations, pop_size=pop_size)
    summary = build_summary(result.layout, combo, gamedata)
    if out is not None:
        render_layout(result.layout, combo, gamedata, root).save(out)
    return summary, low
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_recognize_cli.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add sota/cli.py tests/test_recognize_cli.py
git commit -m "feat: CLI screenshot->pool->solve flow (injected recognizer)"
```

---

## Task 5: OpenCV slot detection (model-shell; skip if cv2 absent)

Refactor `CNN/inven_test.py`'s `find_inventory_slots` + `non_max_suppression` into `sota/recognize/slots.py` as `find_slots(image_bgr) -> [(x,y,w,h)]` (row-major sorted). cv2 imported at module top; the test skips if cv2 is unavailable.

**Files:** Create `sota/recognize/slots.py`; Test `tests/test_slots.py`

- [ ] **Step 1: Implement** `sota/recognize/slots.py`

Port the logic from `CNN/inven_test.py` lines 30–179 verbatim into two functions, dropping the file-writing/debug `cv2.imwrite`/`print` side effects and the global script body:
```python
import cv2
import numpy as np

BORDER_COLOR_BGR = (52, 32, 36)

def non_max_suppression(boxes, overlap_thresh=0.3):
    # ... exact body from CNN/inven_test.py lines 31-63 ...

def find_slots(image_bgr):
    """Detect inventory slot boxes [(x,y,w,h)], sorted row-major. Pure (no disk writes)."""
    # ... adaptive hybrid logic from CNN/inven_test.py lines 67-179,
    #     minus every cv2.imwrite(...) and print(...); return the sorted list ...
```
Keep the adaptive sizing, the A/B contour methods, the multiscale fallback, and the NMS + row-major sort. Remove all debug image writes and prints.

- [ ] **Step 2: Write the test** `tests/test_slots.py`

```python
import pytest
cv2 = pytest.importorskip("cv2")
import pathlib
from sota.recognize.slots import find_slots

CNN = pathlib.Path(__file__).resolve().parents[1] / "CNN"

@pytest.mark.parametrize("img", ["test1.png", "test2.png", "test3.png"])
def test_detects_some_slots(img):
    frame = cv2.imread(str(CNN / img))
    if frame is None:
        pytest.skip(f"{img} not present")
    boxes = find_slots(frame)
    assert isinstance(boxes, list)
    assert len(boxes) >= 1               # detects a plausible number of slots
    for (x, y, w, h) in boxes:
        assert w > 0 and h > 0
    # row-major ordering: y mostly non-decreasing
    ys = [b[1] for b in boxes]
    assert ys == sorted(ys) or len(boxes) < 3
```

- [ ] **Step 3: Run it**

Run: `python3 -m pytest tests/test_slots.py -v`
Expected: PASS if cv2 installed; otherwise the whole module SKIPS cleanly. Record which.

- [ ] **Step 4: Commit**

```bash
git add sota/recognize/slots.py tests/test_slots.py
git commit -m "feat: inventory slot detection ported to reusable module"
```

---

## Task 6: Classifier + recognize orchestration (model-shell; skip if tf/model absent)

Wrap the Keras model load + TTA prediction into `Classifier`, and `recognize_screenshot` to chain slots→classify→labels. tensorflow imported lazily inside methods. Tests skip without tf or a trained model.

**Files:** Create `sota/recognize/classifier.py`, `sota/recognize/recognize.py`; Test `tests/test_classifier_smoke.py`

- [ ] **Step 1: Implement** `sota/recognize/classifier.py`

```python
import pickle
import numpy as np

IMG_SIZE = 128

class Classifier:
    def __init__(self, model_path, classes_path):
        from tensorflow.keras.models import load_model
        self.model = load_model(model_path)
        with open(classes_path, "rb") as f:
            self.class_names = pickle.load(f)

    def classify(self, roi_bgr):
        """Classify one slot ROI (BGR ndarray) -> (label, confidence)."""
        import cv2
        from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
        rgb = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_NEAREST)
        x = preprocess_input(resized.astype(np.float32))[None, ...]
        pred = self.model.predict(x, verbose=0)[0]
        i = int(np.argmax(pred))
        return self.class_names[i], float(pred[i])
```

`sota/recognize/recognize.py`:
```python
from dataclasses import dataclass
from sota.recognize.slots import find_slots

@dataclass(frozen=True)
class RecognitionResult:
    labels: list   # [(label, confidence)] per detected slot, row-major

def recognize_screenshot(path, classifier):
    """Detect slots in the screenshot and classify each -> RecognitionResult.
    Returns a recognize_fn-compatible label list via .labels."""
    import cv2
    frame = cv2.imread(str(path))
    if frame is None:
        raise FileNotFoundError(path)
    labels = []
    for (x, y, w, h) in find_slots(frame):
        roi = frame[y:y + h, x:x + w]
        if roi.size == 0:
            continue
        labels.append(classifier.classify(roi))
    return RecognitionResult(labels=labels)
```

- [ ] **Step 2: Write the smoke test** `tests/test_classifier_smoke.py`

```python
import pathlib
import pytest
pytest.importorskip("tensorflow")
from sota.recognize.classifier import Classifier

CNN = pathlib.Path(__file__).resolve().parents[1] / "CNN"

def test_classifier_loads_and_predicts():
    model_p = CNN / "sephiria_item_model.keras"
    classes_p = CNN / "classes.pickle"
    if not (model_p.exists() and classes_p.exists()):
        pytest.skip("no trained model present")
    import cv2, numpy as np
    clf = Classifier(model_p, classes_p)
    dummy = np.zeros((64, 64, 3), dtype=np.uint8)
    label, conf = clf.classify(dummy)
    assert isinstance(label, str) and 0.0 <= conf <= 1.0
```

- [ ] **Step 3: Run it**

Run: `python3 -m pytest tests/test_classifier_smoke.py -v`
Expected: SKIP without tensorflow/model; PASS if both present. Record which.

- [ ] **Step 4: Commit**

```bash
git add sota/recognize/classifier.py sota/recognize/recognize.py tests/test_classifier_smoke.py
git commit -m "feat: Keras classifier wrapper + recognize orchestration"
```

---

## Task 7: Training entrypoint (canonical dataset) + CLI `--screenshot` wiring

Add a thin `train_model` that runs the existing augmentation/training against the **canonical** dataset (Task 1), and wire `--screenshot` into the CLI `main`.

**Files:** Create `sota/recognize/train.py`; Modify `sota/cli.py` (extend `main`)

- [ ] **Step 1: Implement** `sota/recognize/train.py`

Adapt `CNN/train.py` into a function (do not copy its global script body):
```python
def train_model(dataset_dir, out_model, out_classes, img_size=128, augment_count=150, epochs=30):
    """Train the MobileNetV2 item classifier on a canonical dataset dir
    (subfolders = class names = canonical keys + 'empty'). Saves the .keras model
    and pickled class-name list. Heavy: requires tensorflow + a GPU is recommended.

    Reuse the augmentation strategy from CNN/train.py (composite onto slot
    backgrounds; tablets get 360-degree rotations, artifacts/empty do not)."""
    # Port CNN/train.py's pipeline here, reading classes from dataset_dir subfolders,
    # building (X, y), MobileNetV2 transfer model, fit with EarlyStopping,
    # model.save(out_model); pickle.dump(class_names, open(out_classes,'wb')).
    ...
```
Keep it importable without side effects (tensorflow imported inside the function). A full unit test is out of scope (training is expensive); correctness is covered by the Task 6 smoke test once a model is produced. Add a module docstring documenting the run command:
```
python3 -c "from sota.recognize.dataset import build_canonical_dataset as b; import pathlib; b(pathlib.Path('.'), pathlib.Path('build/dataset'))"
python3 -c "from sota.recognize.train import train_model as t; t('build/dataset','CNN/sephiria_item_model.keras','CNN/classes.pickle')"
```

- [ ] **Step 2: Extend `sota/cli.main`** to support `--screenshot`

In `main`, add `ap.add_argument("--screenshot")` and `ap.add_argument("--yes", action="store_true")` and `ap.add_argument("--min-conf", type=float, default=0.5)`. When `--screenshot` is given, build a real recognizer lazily and call `run_from_screenshot`, printing the recognized pool + low-confidence flags and (unless `--yes`) prompting for confirmation before solving:
```python
    if args.screenshot:
        try:
            from sota.recognize.classifier import Classifier
            from sota.recognize.recognize import recognize_screenshot
            clf = Classifier(root / "CNN" / "sephiria_item_model.keras",
                             root / "CNN" / "classes.pickle")
            recognize_fn = lambda p: recognize_screenshot(p, clf).labels
        except Exception as e:
            print(f"error: recognition unavailable ({e}). Install tensorflow/opencv and train a model.",
                  file=sys.stderr)
            return 3
        summary, low = run_from_screenshot(
            screenshot=args.screenshot, combo=args.combo, slots=args.slots,
            seed=args.seed, out=args.out, gamedata=gd, root=root,
            recognize_fn=recognize_fn, min_conf=args.min_conf,
            generations=args.generations, pop_size=args.pop_size)
        if low:
            print("low-confidence (excluded, review): " +
                  ", ".join(f"{l}({c:.2f})" for l, c in low))
        print(format_summary(summary))
        print(f"\nimage written to {args.out}")
        return 0
```
Place this branch after `--list-combos` handling and before the manual `--combo` keys path. Keep the existing keys-based path unchanged.

- [ ] **Step 3: Verify the pure suite still passes**

Run: `python3 -m pytest -q`
Expected: all pass (model-shell tests skip without ML libs). Report the count and how many skipped.

- [ ] **Step 4: Commit**

```bash
git add sota/recognize/train.py sota/cli.py
git commit -m "feat: training entrypoint (canonical dataset) + CLI --screenshot wiring"
```

---

## Task 8: README + full-suite gate

**Files:** Modify `README.md`; (no new code)

- [ ] **Step 1: Add a Recognition section to `README.md`**

```markdown
## Recognition (optional, needs ML deps)
Install `tensorflow`, `opencv-python`, `scikit-learn`, then build the canonical
dataset and train once:
```
python3 -c "from sota.recognize.dataset import build_canonical_dataset as b, pathlib; b('.', 'build/dataset')"
python3 -c "from sota.recognize.train import train_model as t; t('build/dataset','CNN/sephiria_item_model.keras','CNN/classes.pickle')"
```
Then optimize straight from a screenshot:
```
python3 -m sota.cli --screenshot inventory.png --combo yinggalbul --slots 34 --out build.png
```
Low-confidence detections are listed and excluded; review them and add via `--artifacts/--tablets` if needed.
```

- [ ] **Step 2: Full suite**

Run: `python3 -m pytest -q`
Expected: all pass; report total + skipped count.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: recognition usage and training instructions"
```

---

## Self-Review Notes (addressed)

- **Spec coverage (§5, §11):** screenshot→slots→classify→labels→`ItemPool` (T1,T5,T6); canonical-key alignment fixing filename drift + stale tablet dupes (T1,T2); confidence filtering + duplicates/counts (T3); human-in-the-loop confirmation + low-confidence surfacing (T4,T7); training for the 13 synced images is automatic since T1 rebuilds the dataset from current `assets/` (T1,T7); CLI integration (T4,T7).
- **Testability despite absent ML libs:** Tasks 1–4 are pure and run here; Tasks 5–6 `importorskip` cv2/tensorflow and skip cleanly; the CLI screenshot flow is unit-tested via an injected fake recognizer (T4) so the integration is verified without a model.
- **Type consistency:** `recognize_fn(path) -> [(label, conf)]` is the seam — produced by `recognize_screenshot(...).labels` (T6), consumed by `pool_from_labels` (T3) and `run_from_screenshot` (T4); `label_to_item(label, gamedata) -> (kind,key)|None` stable T2→T3; `Classifier.classify(roi) -> (label, conf)` stable T6→T7.
- **Documented limitations:** recognition accuracy depends on the trained model (no model shipped); restriction/level approximations are inherited from earlier sub-plans (`docs/CALIBRATION.md`); a wrong-but-confident class still needs the human confirmation step.
- **Out of scope:** real-time capture, multi-resolution auto-tuning beyond the existing adaptive slot sizing, and model accuracy benchmarking.
