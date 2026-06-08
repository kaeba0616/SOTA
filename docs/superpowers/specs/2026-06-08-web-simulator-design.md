# Web Placement Simulator — Design

Date: 2026-06-08
Status: Approved (pending spec review)

## Problem

When actually playing Sephiria, deciding **where to place tablets and
artifacts** on the inventory grid is hard and slow. We already have a Python
engine that computes the optimal placement; it just has no accessible UI. This
project wraps that engine in a small website so a player can input the items
they own, pick a target build, and quickly get a recommended layout.

## Goal

A read-only recommendation web app: the user inputs owned items (via screenshot
auto-recognition plus manual correction), selects a target **combo** and an
inventory **slot count**, and the site returns the GA-optimized placement
rendered as an image with a score breakdown.

## Non-goals (v1)

- No drag-to-edit / interactive re-scoring — recommendation is read-only.
- No costume/talent data model — their net effect on placement is the **slot
  count**, which the user enters directly. (Costume presets are a v2 idea.)
- No "miracle" (기적) system.
- No auth, database, persistence, or multi-user concerns — single-user, local.

## Game systems → simulator mapping

| System | In the game | In the simulator |
|---|---|---|
| 콤보 Combo (19) | stat bonus by artifact count | **target build** the user selects |
| 석판 Tablet (54) | placement effects, level deltas | existing engine (unchanged) |
| 아티펙트 Artifact (248) | combo members, level-up targets | existing engine (unchanged) |
| 코스튬 Costume | changes starting slots + special rules | reduced to **slot count** input (v1) |
| 재능 Talent | pre-run growth, can change slots | reduced to **slot count** input (v1) |

Reference: sephiria.wiki, namu.wiki/세피리아.

## Approach

**Chosen: A — Python backend (FastAPI) + thin static HTML/JS frontend.**

Rationale: recognition (TensorFlow CNN), the effect/score engine, the GA solver,
and the PIL renderer are all existing, tested Python (142 passing tests). A
Python server reuses them with zero re-implementation. Read-only output means a
simple request/response cycle.

Rejected:
- **B (static + Pyodide):** TensorFlow CNN does not run in the browser/WASM →
  recognition breaks, forcing a server anyway.
- **C (reimplement engine in JS):** duplicates the just-validated Python engine
  and risks divergence; CNN still needs a server or TF.js conversion.

## Architecture & data flow

```
BROWSER (static front)        FastAPI backend            Existing Python engine
  1 upload screenshot  ──img──▶  POST /api/recognize ──▶  find_slots + Classifier
                       ◀─items─                            (CNN R4 model)
  2 correct low-conf
  3 pick combo + slots
  4 view recommendation ─json─▶  POST /api/solve     ──▶  Pool → GA solve → render
                       ◀png+score                          (model/evaluate/solve/render)
       (catalog dropdowns)  ◀──  GET  /api/catalog   ──▶  data/*.json
```

Models (gamedata + CNN Classifier) load **once at server startup** and are
reused across requests.

## Components (file structure)

```
sota/web/
  __init__.py
  app.py        # FastAPI app: routing + static mount; loads gamedata + Classifier at startup
  services.py   # orchestration bridge (web <-> engine), returns plain dicts
  schemas.py    # Pydantic request/response models
  static/
    index.html  # the 4-step UI
    app.js      # fetch calls + client state + DOM rendering
    style.css
```

Run: `uvicorn sota.web.app:app` (add a `python -m sota.web` entry as convenience).

Unit responsibilities (each does one thing):

| Unit | Responsibility | Depends on |
|---|---|---|
| `app.py` | HTTP parse/respond only; holds startup-loaded models in app state | services, schemas |
| `services.py` | `recognize_image(bytes) -> items`, `solve(req) -> result`; calls existing engine | recognize, solve, render, data |
| `schemas.py` | typed request/response contracts | — |
| `static/*` | frontend UI | the API |

## API & data contracts

`GET /api/catalog` → `{combos:[{key,name}], artifacts:[{key,name}], tablets:[{key,name}]}`
(used to populate correction dropdowns and the combo selector).

`POST /api/recognize` (multipart image) →
`{items:[RecognizeItem], note?}` where
`RecognizeItem = {slot:int, row:int, col:int, type:"artifact"|"tablet"|"empty", key:str, confidence:float}`.
Recognition yields the **multiset of owned items**; positions are informational.

`POST /api/solve` (JSON `SolveRequest`) → `SolveResult`:
- `SolveRequest = {tablets:[key], artifacts:[key], combo:key, slots:int, seed?:int, generations?:int, pop_size?:int}`
- `SolveResult = {score:int, combo_stages:int, level_sum:int, placements:[{key,row,col,level}], image_base64:str}`

The recognized/corrected item multiset becomes the GA **pool**; the solver places
it on a fresh `slots`-sized grid (same flow as the existing `pool_from_labels` →
GA path). `slots` may differ from the screenshot's slot count.

## Frontend UX (4 steps)

1. **Upload** a screenshot → calls `/api/recognize` → renders the recognized
   items, low-confidence ones highlighted for review.
2. **Correct** — edit any item via a searchable dropdown from `/api/catalog`;
   add/remove items so the owned multiset is right.
3. **Target** — pick a combo (dropdown, 19) and enter slot count.
4. **Recommend** — calls `/api/solve` → shows the rendered placement image and
   the score breakdown (combo stages × 1000 + level sum).

Solve is disabled until a combo and a valid slot count are set.

## Error handling

- `/api/recognize`: non-image / decode failure → 400; zero slots found → 200
  with empty items and a note.
- `/api/solve`: unknown combo or item key → 400 naming the offender; slot count
  outside `[min,max]` → 400; `generations`/`pop_size` capped to a safe maximum to
  prevent runaway; GA failure → 500 with message.
- Startup: missing model/classes file → fail fast with a clear log message.
- Frontend: inline error banners; never silently drop a failed request.

## Testing

- `tests/test_web_api.py` (FastAPI `TestClient`):
  - `/api/catalog` → counts 19 / 248 / 54.
  - `/api/recognize` with `CNN/test1.png` → 30 items, each with a confidence.
  - `/api/solve` with the known firmness item set + slots → `score > 0`, image
    present, every placement inside the grid.
  - error cases: unknown combo → 400; bad slot count → 400.
- `services.py` unit tests against a fixture image and a fixed item list.
- Existing 142 engine tests remain untouched and must keep passing.

## Dependencies

Add: `fastapi`, `uvicorn`, `python-multipart` (uploads), `httpx` (TestClient).

## Future (v2+)

- Costume/talent presets that auto-set slot count and special placement rules
  (requires collecting costume/talent data from the wiki).
- Drag-to-edit with live re-scoring.
- "Miracle" system support.
- Auto-recommend best combo across all 19 (the manual analysis done for
  test1/2/3) as an optional "decide for me" mode.
