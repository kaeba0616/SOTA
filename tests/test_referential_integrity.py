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
    SHAPES = {"row", "column", "diagonal", "top", "bottom"}
    for t in _load("tablets.json"):
        assert "_TODO_geometry" not in t, f"{t['key']} still missing geometry"
        for e in t["effects"]:
            assert "type" in e and "value" in e, f"{t['key']}: effect missing type/value"
            has_pos = "pos" in e
            has_shape = "shape" in e
            assert has_pos != has_shape, f"{t['key']}: effect must have exactly one of pos/shape: {e}"
            if has_pos:
                assert len(e["pos"]) == 2
            else:
                assert e["shape"] in SHAPES, f"{t['key']}: unknown shape {e['shape']}"

def test_max_level_is_at_least_one():
    assert all(a["max_level"] >= 1 for a in _load("artifacts.json"))

def test_every_artifact_resolves_to_a_unique_image():
    import os
    from collections import Counter
    idmap = _load("idmap.json")
    arts = _load("artifacts.json")
    assert idmap["missing"] == [], f"artifacts without local image: {idmap['missing']}"
    assert len(idmap["map"]) == len(arts) == 248
    dupes = {f: ks for f, ks in
             ((f, [k for k in idmap["map"] if idmap["map"][k] == f]) for f in set(idmap["map"].values()))
             if len(ks) > 1}
    assert not dupes, f"multiple artifacts share one image: {dupes}"
    imgdir = DATA.parents[1] / "assets" / "artifacts"
    have = {os.path.splitext(f)[0] for f in os.listdir(imgdir)}
    unresolved = [v for v in idmap["map"].values() if v not in have]
    assert not unresolved, f"mapped images not on disk: {unresolved[:5]}"

def test_every_tablet_resolves_to_an_image():
    import os
    imgdir = DATA.parents[1] / "assets" / "tablets"
    have = {os.path.splitext(f)[0] for f in os.listdir(imgdir)}
    missing = [t["key"] for t in _load("tablets.json") if t["key"] not in have]
    assert not missing, f"tablets without image: {missing}"
