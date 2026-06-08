import pathlib

from fastapi import FastAPI, HTTPException, UploadFile, File
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


@app.post("/api/recognize")
def recognize_endpoint(file: UploadFile = File(...)):
    data = file.file.read()
    try:
        items = services.recognize_image(data, _classifier(), GAMEDATA)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"items": items, "note": None if items else "no slots detected"}


# Static frontend mounted last so /api/* routes take precedence.
app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
