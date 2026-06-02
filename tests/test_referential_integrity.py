import json, pathlib
import pytest

DATA = pathlib.Path(__file__).resolve().parents[1] / "sota" / "data"

def _load(name):
    p = DATA / name
    if not p.exists():
        pytest.skip(f"{name} not generated yet — run the fetchers first")
    return json.loads(p.read_text(encoding="utf-8"))

def test_counts():
    assert len(_load("artifacts.json")) == 248
    assert len(_load("combos.json")) == 19
    assert len(_load("tablets.json")) == 54

def test_every_artifact_combo_is_defined():
    combo_keys = {c["key"] for c in _load("combos.json")}
    arts = _load("artifacts.json")
    referenced = {c for a in arts for c in a["combos"]}
    assert referenced <= combo_keys, f"undefined combos: {referenced - combo_keys}"

def test_combo_thresholds_are_within_bounds():
    for c in _load("combos.json"):
        counts = [t["count"] for t in c["thresholds"]]
        assert counts == sorted(counts)
        assert min(counts) >= c["min_count"] and max(counts) <= c["max_count"]

def test_every_tablet_has_well_formed_effects():
    for t in _load("tablets.json"):
        assert "_TODO_geometry" not in t, f"{t['key']} still missing geometry"
        for e in t["effects"]:
            assert set(e) >= {"pos", "type", "value"}
            assert len(e["pos"]) == 2

def test_max_level_is_at_least_one():
    assert all(a["max_level"] >= 1 for a in _load("artifacts.json"))

def test_every_artifact_resolves_to_an_image():
    idmap = _load("idmap.json")
    assert idmap["missing"] == [], f"artifacts without local image: {idmap['missing']}"
