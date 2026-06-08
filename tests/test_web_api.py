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
