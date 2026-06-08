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
