import json, pathlib
from sota.scrape.tablet_normalize import normalize_tablet

FIX = pathlib.Path(__file__).parent / "fixtures"

def _load():
    return json.loads((FIX / "legacy_tablets_sample.json").read_text(encoding="utf-8"))

def test_can_rotate_typo_becomes_rotatable():
    t = normalize_tablet(_load()[0])
    assert t["rotatable"] is True
    assert t["key"] == "approximation"

def test_rename_applied_from_image_basename():
    t = normalize_tablet(_load()[1])  # arrival -> advent
    assert t["key"] == "advent"
    assert t["name"] == "도래"
    assert t["effects"] == [{"pos": [0, -1], "type": "level_add", "value": -1}]

def test_full_schema_keys():
    t = normalize_tablet(_load()[0])
    assert set(t) == {"id", "key", "name", "image", "rotatable", "size", "rarity", "restriction", "effects"}
