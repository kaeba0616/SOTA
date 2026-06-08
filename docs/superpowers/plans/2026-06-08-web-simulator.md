# Web Placement Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A read-only web app where a player inputs owned tablets/artifacts (screenshot auto-recognition + manual correction), picks a target combo and slot count, and gets the GA-optimized placement rendered as an image with a score breakdown.

**Architecture:** A FastAPI backend reuses the existing, tested Python engine (CNN recognition, effect/score engine, GA solver, PIL renderer) behind three JSON/multipart endpoints (`/api/catalog`, `/api/recognize`, `/api/solve`). A thin static HTML/JS frontend drives the 4-step flow. The compute logic is entirely existing code; only HTTP routing and the UI are new.

**Tech Stack:** Python 3.12, FastAPI, Uvicorn, Pydantic, python-multipart (uploads), httpx (TestClient); existing engine modules under `sota/`; vanilla HTML/CSS/JS frontend.

---

## File structure

```
sota/web/
  __init__.py        # empty package marker
  schemas.py         # Pydantic SolveRequest (input validation)
  services.py        # solve_build(...) and recognize_image(...) — bridge web <-> engine
  app.py             # FastAPI app: GAMEDATA load, 3 routes, static mount, lazy CNN
  __main__.py        # `python -m sota.web` -> uvicorn runner
  static/
    index.html       # 4-step UI
    app.js           # fetch calls + client state + DOM rendering
    style.css        # minimal styling
tests/
  test_web_services.py  # unit: solve_build, recognize_image
  test_web_api.py       # API: catalog/solve/recognize via TestClient
```

Reused engine APIs (do not modify):
- `sota.model.gamedata.load_game_data()` → `gd` with dict attrs `gd.combos` (`{key:{label,...}}`), `gd.artifacts` (`{key:{name_kor,combos,max_level,...}}`), `gd.tablets` (`{key:{name,...}}`).
- `sota.model.pool.ItemPool(tablets=[...], artifacts=[...])`.
- `sota.solve.ga.solve(pool, combo, slot_count, gamedata, seed, generations, pop_size)` → `result` with `result.layout`.
- `sota.render.summary.build_summary(layout, combo, gamedata)` → dict `{combo, score, stages, level_sum, targets[], tablets[], approximated[]}`.
- `sota.render.grid_image.render_layout(layout, combo, gamedata, root)` → PIL `Image` (`.save(...)`).
- `sota.recognize.slots.find_slots(frame)` → list of `(x, y, w, h)`.
- `sota.recognize.classifier.Classifier(model_path, classes_path)` with `.classify(roi_bgr)` → `(key, confidence)`.
- `sota.recognize.keymap.label_to_item(label, gd)` → `("tablet"|"artifact", key)` or `None`.

---

## Task 0: Package skeleton and dependencies

**Files:**
- Create: `sota/web/__init__.py`
- Modify: `pyproject.toml:5-8`

- [ ] **Step 1: Create the package marker**

Create `sota/web/__init__.py`:

```python
"""Web placement simulator (FastAPI app over the existing engine)."""
```

- [ ] **Step 2: Add the optional `web` dependency group**

In `pyproject.toml`, replace the `[project.optional-dependencies]` block (lines 7-8) with:

```toml
[project.optional-dependencies]
dev = ["pytest>=8.0", "httpx>=0.27"]
web = ["fastapi>=0.110", "uvicorn>=0.29", "python-multipart>=0.0.9"]
```

- [ ] **Step 3: Install the new deps**

Run: `pip install -e ".[dev,web]"`
Expected: installs fastapi, uvicorn, python-multipart, httpx without error.

- [ ] **Step 4: Verify FastAPI imports**

Run: `python -c "import fastapi, uvicorn, multipart, httpx; print('ok')"`
Expected: prints `ok`.

- [ ] **Step 5: Commit**

```bash
git add sota/web/__init__.py pyproject.toml
git commit -m "chore(web): add web package skeleton and optional deps"
```

---

## Task 1: Request schema (`schemas.py`)

**Files:**
- Create: `sota/web/schemas.py`
- Test: `tests/test_web_services.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_web_services.py`:

```python
from sota.web.schemas import SolveRequest


def test_solve_request_defaults():
    req = SolveRequest(combo="firmness", slots=34)
    assert req.tablets == []
    assert req.artifacts == []
    assert req.seed == 0
    assert req.generations == 60
    assert req.pop_size == 40


def test_solve_request_accepts_items():
    req = SolveRequest(combo="firmness", slots=30,
                       tablets=["agglutination"], artifacts=["amulet_of_power"])
    assert req.tablets == ["agglutination"]
    assert req.artifacts == ["amulet_of_power"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_web_services.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sota.web.schemas'`.

- [ ] **Step 3: Write the schema**

Create `sota/web/schemas.py`:

```python
from pydantic import BaseModel, Field


class SolveRequest(BaseModel):
    tablets: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    combo: str
    slots: int
    seed: int = 0
    generations: int = 60
    pop_size: int = 40
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_web_services.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add sota/web/schemas.py tests/test_web_services.py
git commit -m "feat(web): SolveRequest schema"
```

---

## Task 2: Solve service (`services.solve_build`)

**Files:**
- Create: `sota/web/services.py`
- Test: `tests/test_web_services.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_web_services.py`:

```python
import base64
import pathlib
import pytest
from sota.model.gamedata import load_game_data
from sota.web import services

ROOT = pathlib.Path(__file__).resolve().parents[1]
GD = load_game_data()

# Known firmness artifacts present in test1 inventory.
FIRMNESS_ARTS = ["amulet_of_power", "mark_of_warrior",
                 "shield_technique_manual", "absolute_ring"]


def test_solve_build_returns_score_and_image():
    out = services.solve_build(
        tablets=["agglutination", "agglutination"], artifacts=FIRMNESS_ARTS,
        combo="firmness", slots=34, seed=42, generations=40, pop_size=60,
        gamedata=GD, root=ROOT)
    assert out["combo"] == "firmness"
    assert out["score"] > 0
    assert out["stages"] >= 1
    # image is valid base64 PNG
    raw = base64.b64decode(out["image_base64"])
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    # every placement sits on the grid
    for t in out["targets"]:
        assert 0 <= t["cell"][0] and 0 <= t["cell"][1] < 6


def test_solve_build_rejects_unknown_combo():
    with pytest.raises(ValueError, match="unknown combo"):
        services.solve_build(tablets=[], artifacts=[], combo="nope", slots=34,
                             seed=0, generations=10, pop_size=10,
                             gamedata=GD, root=ROOT)


def test_solve_build_rejects_unknown_key():
    with pytest.raises(ValueError, match="unknown keys"):
        services.solve_build(tablets=["not_a_tablet"], artifacts=[],
                             combo="firmness", slots=34, seed=0,
                             generations=10, pop_size=10, gamedata=GD, root=ROOT)


def test_solve_build_rejects_bad_slots():
    with pytest.raises(ValueError, match="slots out of range"):
        services.solve_build(tablets=[], artifacts=[], combo="firmness",
                             slots=0, seed=0, generations=10, pop_size=10,
                             gamedata=GD, root=ROOT)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_web_services.py -k solve_build -v`
Expected: FAIL with `AttributeError: module 'sota.web.services' has no attribute 'solve_build'` (or ModuleNotFound).

- [ ] **Step 3: Write the service**

Create `sota/web/services.py`:

```python
import base64
import io

from sota.model.pool import ItemPool
from sota.solve.ga import solve
from sota.render.summary import build_summary
from sota.render.grid_image import render_layout


def solve_build(*, tablets, artifacts, combo, slots, seed, generations,
                pop_size, gamedata, root):
    """Run the GA solver and return build_summary(...) plus a base64 PNG.

    Raises ValueError (-> HTTP 400) for unknown combo/keys or bad slot count.
    generations/pop_size are clamped to a safe maximum to prevent runaway.
    """
    if not (1 <= slots <= 60):
        raise ValueError(f"slots out of range: {slots} (expected 1..60)")
    bad_t = [k for k in tablets if k not in gamedata.tablets]
    bad_a = [k for k in artifacts if k not in gamedata.artifacts]
    if bad_t or bad_a:
        raise ValueError(f"unknown keys: tablets={bad_t} artifacts={bad_a}")
    if combo not in gamedata.combos:
        raise ValueError(f"unknown combo: {combo}")

    generations = max(1, min(int(generations), 300))
    pop_size = max(1, min(int(pop_size), 300))

    pool = ItemPool(tablets=list(tablets), artifacts=list(artifacts))
    result = solve(pool, combo, slot_count=slots, gamedata=gamedata,
                   seed=seed, generations=generations, pop_size=pop_size)
    summary = build_summary(result.layout, combo, gamedata)

    img = render_layout(result.layout, combo, gamedata, root)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    summary["image_base64"] = base64.b64encode(buf.getvalue()).decode("ascii")
    return summary
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_web_services.py -k solve_build -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add sota/web/services.py tests/test_web_services.py
git commit -m "feat(web): solve_build service (GA + render -> summary + base64 PNG)"
```

---

## Task 3: Recognize service (`services.recognize_image`)

**Files:**
- Modify: `sota/web/services.py`
- Test: `tests/test_web_services.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_web_services.py`:

```python
from sota.recognize.classifier import Classifier

CLF = None


def _classifier():
    global CLF
    if CLF is None:
        CLF = Classifier(ROOT / "CNN" / "sephiria_item_model.keras",
                         ROOT / "CNN" / "classes.pickle")
    return CLF


def test_recognize_image_on_test1():
    img_bytes = (ROOT / "CNN" / "test1.png").read_bytes()
    items = services.recognize_image(img_bytes, _classifier(), GD)
    assert len(items) == 30
    first = items[0]
    assert set(first) == {"slot", "row", "col", "type", "key", "confidence"}
    assert first["type"] in {"artifact", "tablet", "empty"}
    assert 0.0 <= first["confidence"] <= 1.0


def test_recognize_image_rejects_garbage():
    with pytest.raises(ValueError, match="could not decode"):
        services.recognize_image(b"not an image", _classifier(), GD)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_web_services.py -k recognize_image -v`
Expected: FAIL with `AttributeError: module 'sota.web.services' has no attribute 'recognize_image'`.

- [ ] **Step 3: Add the recognize service**

Append to `sota/web/services.py`:

```python
import numpy as np

from sota.recognize.slots import find_slots
from sota.recognize.keymap import label_to_item


def recognize_image(image_bytes, classifier, gamedata):
    """Decode an uploaded screenshot, detect slots, classify each.

    Returns a list of dicts in row-major order:
      {slot, row, col, type, key, confidence}
    type is the keymap kind ("tablet"/"artifact") or "empty" for empty/unknown.
    Raises ValueError (-> HTTP 400) if the bytes are not a decodable image.
    """
    import cv2
    frame = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("could not decode image")
    boxes = sorted(find_slots(frame), key=lambda b: (round(b[1] / 100), b[0]))
    items = []
    for i, (x, y, w, h) in enumerate(boxes):
        roi = frame[y:y + h, x:x + w]
        if roi.size == 0:
            continue
        key, conf = classifier.classify(roi)
        item = label_to_item(key, gamedata)
        typ = "empty" if item is None else item[0]
        items.append({"slot": i, "row": i // 6, "col": i % 6,
                      "type": typ, "key": key, "confidence": float(conf)})
    return items
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_web_services.py -k recognize_image -v`
Expected: PASS (2 passed). Note: first run loads the CNN model (~seconds).

- [ ] **Step 5: Commit**

```bash
git add sota/web/services.py tests/test_web_services.py
git commit -m "feat(web): recognize_image service (bytes -> recognized items)"
```

---

## Task 4: FastAPI app — catalog + solve (`app.py`)

**Files:**
- Create: `sota/web/app.py`
- Test: `tests/test_web_api.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_web_api.py`:

```python
from fastapi.testclient import TestClient
from sota.web.app import app

client = TestClient(app)


def test_catalog_counts():
    r = client.get("/api/catalog")
    assert r.status_code == 200
    body = r.json()
    assert len(body["combos"]) == 19
    assert len(body["artifacts"]) == 248
    assert len(body["tablets"]) == 54
    assert set(body["combos"][0]) == {"key", "name"}


def test_solve_firmness():
    r = client.post("/api/solve", json={
        "tablets": ["agglutination", "agglutination"],
        "artifacts": ["amulet_of_power", "mark_of_warrior",
                      "shield_technique_manual", "absolute_ring"],
        "combo": "firmness", "slots": 34, "seed": 42,
        "generations": 40, "pop_size": 60})
    assert r.status_code == 200
    body = r.json()
    assert body["score"] > 0
    assert body["image_base64"]


def test_solve_unknown_combo_is_400():
    r = client.post("/api/solve", json={"combo": "nope", "slots": 34})
    assert r.status_code == 400
    assert "unknown combo" in r.json()["detail"]


def test_solve_bad_slots_is_400():
    r = client.post("/api/solve", json={"combo": "firmness", "slots": 0})
    assert r.status_code == 400
    assert "slots out of range" in r.json()["detail"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_web_api.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sota.web.app'`.

- [ ] **Step 3: Write the app (catalog + solve + static mount)**

Create `sota/web/app.py`:

```python
import pathlib

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from sota.model.gamedata import load_game_data
from sota.web import services
from sota.web.schemas import SolveRequest

ROOT = pathlib.Path(__file__).resolve().parents[2]
STATIC = pathlib.Path(__file__).parent / "static"

app = FastAPI(title="Sephiria Placement Simulator")

# Game data is pure JSON — cheap to load at import. The CNN model is heavy, so
# it is loaded lazily on the first /api/recognize call.
GAMEDATA = load_game_data()
_classifier_cache = {}


def _classifier():
    if "clf" not in _classifier_cache:
        from sota.recognize.classifier import Classifier
        _classifier_cache["clf"] = Classifier(
            ROOT / "CNN" / "sephiria_item_model.keras",
            ROOT / "CNN" / "classes.pickle")
    return _classifier_cache["clf"]


@app.get("/api/catalog")
def catalog():
    return {
        "combos": [{"key": k, "name": c["label"]} for k, c in GAMEDATA.combos.items()],
        "artifacts": [{"key": k, "name": a["name_kor"]} for k, a in GAMEDATA.artifacts.items()],
        "tablets": [{"key": k, "name": t["name"]} for k, t in GAMEDATA.tablets.items()],
    }


@app.post("/api/solve")
def solve_endpoint(req: SolveRequest):
    try:
        return services.solve_build(
            tablets=req.tablets, artifacts=req.artifacts, combo=req.combo,
            slots=req.slots, seed=req.seed, generations=req.generations,
            pop_size=req.pop_size, gamedata=GAMEDATA, root=ROOT)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Static frontend mounted last so /api/* routes take precedence.
app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
```

- [ ] **Step 4: Create a placeholder static dir so the mount succeeds**

Create `sota/web/static/index.html` (replaced fully in Task 6):

```html
<!doctype html><meta charset="utf-8"><title>Sephiria Placement Simulator</title>
<p>placeholder</p>
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_web_api.py -v`
Expected: PASS (4 passed).

- [ ] **Step 6: Commit**

```bash
git add sota/web/app.py sota/web/static/index.html tests/test_web_api.py
git commit -m "feat(web): FastAPI app with /api/catalog and /api/solve"
```

---

## Task 5: Recognize endpoint (`POST /api/recognize`)

**Files:**
- Modify: `sota/web/app.py`
- Test: `tests/test_web_api.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_web_api.py`:

```python
import pathlib as _pl

ROOT = _pl.Path(__file__).resolve().parents[1]


def test_recognize_endpoint_on_test1():
    img = (ROOT / "CNN" / "test1.png").read_bytes()
    r = client.post("/api/recognize",
                    files={"file": ("test1.png", img, "image/png")})
    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) == 30
    assert set(body["items"][0]) == {"slot", "row", "col", "type", "key", "confidence"}


def test_recognize_endpoint_rejects_garbage():
    r = client.post("/api/recognize",
                    files={"file": ("x.png", b"not an image", "image/png")})
    assert r.status_code == 400
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_web_api.py -k recognize -v`
Expected: FAIL with 404 (route not defined) on the first test.

- [ ] **Step 3: Add the recognize endpoint**

In `sota/web/app.py`, add the import and route. Change the import line:

```python
from fastapi import FastAPI, HTTPException, UploadFile, File
```

Then add this route immediately before the `app.mount(...)` line:

```python
@app.post("/api/recognize")
def recognize_endpoint(file: UploadFile = File(...)):
    data = file.file.read()
    try:
        items = services.recognize_image(data, _classifier(), GAMEDATA)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"items": items, "note": None if items else "no slots detected"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_web_api.py -k recognize -v`
Expected: PASS (2 passed). First run loads the CNN model.

- [ ] **Step 5: Commit**

```bash
git add sota/web/app.py tests/test_web_api.py
git commit -m "feat(web): POST /api/recognize endpoint"
```

---

## Task 6: Frontend (4-step UI)

**Files:**
- Create/replace: `sota/web/static/index.html`
- Create: `sota/web/static/app.js`
- Create: `sota/web/static/style.css`
- Test: `tests/test_web_api.py` (append a static-serving smoke test)

- [ ] **Step 1: Write the failing smoke test**

Append to `tests/test_web_api.py`:

```python
def test_index_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "Sephiria" in r.text


def test_appjs_served():
    r = client.get("/app.js")
    assert r.status_code == 200
    assert "api/solve" in r.text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_web_api.py -k "index_served or appjs_served" -v`
Expected: FAIL — `/app.js` 404 and/or index text missing.

- [ ] **Step 3: Write `style.css`**

Create `sota/web/static/style.css`:

```css
body { font-family: system-ui, sans-serif; max-width: 880px; margin: 24px auto;
       padding: 0 16px; background: #1d1b24; color: #e8e6ee; }
h1 { font-size: 20px; } h2 { font-size: 16px; margin-top: 24px; }
.step { border: 1px solid #3a3744; border-radius: 8px; padding: 12px 16px; margin: 12px 0; }
.row { display: flex; gap: 8px; align-items: center; margin: 4px 0; }
.row.low { background: #4a2d2d; }
select, input, button { padding: 6px 8px; background: #2a2833; color: #e8e6ee;
       border: 1px solid #4a4757; border-radius: 6px; }
button { cursor: pointer; } button:disabled { opacity: 0.5; cursor: default; }
.err { color: #ff9a9a; margin: 8px 0; }
.conf { font-size: 12px; color: #9a97a8; min-width: 48px; }
#result img { max-width: 100%; border: 1px solid #3a3744; border-radius: 8px; }
.muted { color: #9a97a8; font-size: 13px; }
```

- [ ] **Step 4: Write `index.html`**

Create `sota/web/static/index.html`:

```html
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sephiria Placement Simulator</title>
  <link rel="stylesheet" href="/style.css">
</head>
<body>
  <h1>Sephiria 배치 추천</h1>
  <div id="err" class="err"></div>

  <div class="step">
    <h2>1. 스크린샷 업로드 (선택)</h2>
    <input type="file" id="file" accept="image/*">
    <button id="recognizeBtn">인식</button>
    <p class="muted">업로드하면 자동 인식합니다. 없으면 2단계에서 직접 추가하세요.</p>
  </div>

  <div class="step">
    <h2>2. 보유 아이템 (저신뢰 항목은 빨간 배경 — 확인/수정)</h2>
    <div id="items"></div>
    <div class="row">
      <input list="catalog" id="addKey" placeholder="키 입력 (예: amulet_of_power)">
      <datalist id="catalog"></datalist>
      <button id="addBtn">추가</button>
    </div>
  </div>

  <div class="step">
    <h2>3. 목표 콤보 & 슬롯 수</h2>
    <div class="row">
      콤보 <select id="combo"></select>
      슬롯 <input type="number" id="slots" value="34" min="1" max="60">
    </div>
  </div>

  <div class="step">
    <h2>4. 추천 받기</h2>
    <button id="solveBtn" disabled>추천 배치 계산</button>
    <div id="result"></div>
  </div>

  <script src="/app.js"></script>
</body>
</html>
```

- [ ] **Step 5: Write `app.js`**

Create `sota/web/static/app.js`:

```javascript
const state = { items: [], catalog: { combos: [], artifacts: [], tablets: [] } };
const $ = (id) => document.getElementById(id);
const showErr = (m) => { $("err").textContent = m || ""; };

function keyType(key) {
  if (state.catalog.tablets.some((t) => t.key === key)) return "tablet";
  if (state.catalog.artifacts.some((a) => a.key === key)) return "artifact";
  return "empty";
}

function renderItems() {
  const box = $("items");
  box.innerHTML = "";
  state.items.forEach((it, i) => {
    const row = document.createElement("div");
    row.className = "row" + (it.confidence < 0.9 ? " low" : "");
    const inp = document.createElement("input");
    inp.value = it.key; inp.setAttribute("list", "catalog");
    inp.onchange = () => { it.key = inp.value; it.type = keyType(inp.value); };
    const conf = document.createElement("span");
    conf.className = "conf";
    conf.textContent = it.confidence != null ? it.confidence.toFixed(2) : "";
    const del = document.createElement("button");
    del.textContent = "삭제";
    del.onclick = () => { state.items.splice(i, 1); renderItems(); };
    row.append(inp, conf, del);
    box.appendChild(row);
  });
  $("solveBtn").disabled = !$("combo").value;
}

async function loadCatalog() {
  const r = await fetch("/api/catalog");
  state.catalog = await r.json();
  $("combo").innerHTML = state.catalog.combos
    .map((c) => `<option value="${c.key}">${c.name} (${c.key})</option>`).join("");
  $("catalog").innerHTML = [...state.catalog.tablets, ...state.catalog.artifacts]
    .map((x) => `<option value="${x.key}">${x.name}</option>`).join("");
  renderItems();
}

async function recognize() {
  showErr("");
  const f = $("file").files[0];
  if (!f) { showErr("파일을 선택하세요."); return; }
  const fd = new FormData(); fd.append("file", f);
  const r = await fetch("/api/recognize", { method: "POST", body: fd });
  if (!r.ok) { showErr("인식 실패: " + (await r.json()).detail); return; }
  const body = await r.json();
  state.items = body.items.filter((it) => it.type !== "empty");
  renderItems();
}

function addItem() {
  const key = $("addKey").value.trim();
  if (!key) return;
  state.items.push({ key, type: keyType(key), confidence: 1.0 });
  $("addKey").value = "";
  renderItems();
}

async function solve() {
  showErr("");
  const payload = {
    tablets: state.items.filter((i) => i.type === "tablet").map((i) => i.key),
    artifacts: state.items.filter((i) => i.type === "artifact").map((i) => i.key),
    combo: $("combo").value,
    slots: parseInt($("slots").value, 10),
    seed: 42, generations: 60, pop_size: 80,
  };
  $("solveBtn").disabled = true; $("solveBtn").textContent = "계산 중…";
  const r = await fetch("/api/solve",
    { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload) });
  $("solveBtn").disabled = false; $("solveBtn").textContent = "추천 배치 계산";
  if (!r.ok) { showErr("계산 실패: " + (await r.json()).detail); return; }
  const s = await r.json();
  $("result").innerHTML =
    `<p>점수 <b>${s.score}</b> (콤보 ${s.stages}단계 × 1000 + 레벨 ${s.level_sum})</p>` +
    `<img src="data:image/png;base64,${s.image_base64}">`;
}

$("recognizeBtn").onclick = recognize;
$("addBtn").onclick = addItem;
$("solveBtn").onclick = solve;
$("combo").onchange = renderItems;
loadCatalog();
```

- [ ] **Step 6: Run the smoke test to verify it passes**

Run: `pytest tests/test_web_api.py -k "index_served or appjs_served" -v`
Expected: PASS (2 passed).

- [ ] **Step 7: Manual end-to-end verification**

Run: `python -m sota.web` (added in Task 7; until then run `uvicorn sota.web.app:app --port 8000`).
Open `http://localhost:8000`. Verify:
- combo dropdown lists 19 combos.
- Upload `CNN/test1.png`, click 인식 → ~rows appear, low-confidence rows have a red background.
- Pick combo `firmness`, slots 34, click 추천 배치 계산 → score line + placement image appear.

- [ ] **Step 8: Commit**

```bash
git add sota/web/static/ tests/test_web_api.py
git commit -m "feat(web): 4-step frontend (upload, correct, target, recommend)"
```

---

## Task 7: Run entry point and README

**Files:**
- Create: `sota/web/__main__.py`
- Modify: `README.md`

- [ ] **Step 1: Write the runner**

Create `sota/web/__main__.py`:

```python
"""Run the web simulator: python -m sota.web [--host H] [--port P]"""
import argparse

import uvicorn


def main():
    ap = argparse.ArgumentParser(prog="sota.web")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    uvicorn.run("sota.web.app:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify it boots and serves**

Run: `python -m sota.web --port 8765 &` then `sleep 3 && curl -s localhost:8765/api/catalog | head -c 40 && kill %1`
Expected: prints the start of a JSON catalog payload (e.g. `{"combos":[...`).

- [ ] **Step 3: Document it in the README**

Add this section to `README.md` (append at the end):

```markdown
## Web placement simulator

Install web deps and run the local site:

    pip install -e ".[web]"
    python -m sota.web            # http://127.0.0.1:8000

Upload an inventory screenshot (or add items by key), pick a target combo and
slot count, and get the GA-optimized placement. Recognition needs the CNN model
under `CNN/` plus tensorflow + opencv installed.
```

- [ ] **Step 4: Commit**

```bash
git add sota/web/__main__.py README.md
git commit -m "feat(web): python -m sota.web entry point + README"
```

---

## Task 8: Full suite and merge

- [ ] **Step 1: Run the whole test suite**

Run: `pytest -q`
Expected: all existing 142 tests plus the new web tests pass (web tests that load the CNN model take a few seconds on first run).

- [ ] **Step 2: Merge the feature branch to main**

```bash
git checkout main
git merge --no-ff <feature-branch> -m "Merge web-simulator: FastAPI placement recommendation site"
```

---

## Self-review notes

- **Spec coverage:** input via screenshot+correction (Tasks 3,5,6), combo+slot selection (Task 6 step 4–5; validated Task 2), read-only recommendation image+score (Tasks 2,6), catalog dropdowns (Task 4), error handling 400s (Tasks 2,4,5), tests incl. existing 142 untouched (Task 8), deps (Task 0). Costume/talent reduced to slot input; miracle excluded — no tasks, as designed.
- **Types consistent:** `solve_build`/`recognize_image` signatures match between `services.py` and their call sites in `app.py`; `SolveRequest` fields match the `solve_build` kwargs; frontend payload keys (`tablets, artifacts, combo, slots, seed, generations, pop_size`) match `SolveRequest`.
- **No placeholders:** all code blocks are complete; the Task 4 placeholder `index.html` is intentionally and fully replaced in Task 6.
