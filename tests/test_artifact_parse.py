from sota.scrape.artifact_parse import parse_content

def test_single_ladder_four_levels():
    r = parse_content("부여된 콤보와 관련된 속성 피해 +2/4/6/8")
    assert r["max_level"] == 4
    assert r["scale_groups"] == [[2.0, 4.0, 6.0, 8.0]]

def test_percent_ladder_three_levels():
    r = parse_content("잎 획득량 +10/25/50%")
    assert r["max_level"] == 3
    assert r["scale_groups"] == [[10.0, 25.0, 50.0]]

def test_no_ladder_is_level_one():
    r = parse_content("[고유] 파이어 볼트 획득")
    assert r["max_level"] == 1
    assert r["scale_groups"] == []

def test_multiline_takes_longest_ladder():
    r = parse_content("화상 부여 시 0/1/1/2회 추가 부여\n화상 중첩 +1/1/1/2")
    assert r["max_level"] == 4
    assert [2.0] not in r["scale_groups"]
    assert len(r["scale_groups"]) == 2

def test_decimal_ladder():
    r = parse_content("치명타 확률 1/1.5/2/2.5% 증가")
    assert r["max_level"] == 4
    assert r["scale_groups"] == [[1.0, 1.5, 2.0, 2.5]]

import json, pathlib
from sota.scrape.artifact_parse import normalize_artifact

FIX = pathlib.Path(__file__).parent / "fixtures"

def test_normalize_artifact_schema():
    raw = json.loads((FIX / "raw_artifacts_sample.json").read_text(encoding="utf-8"))
    a = normalize_artifact(raw[1])  # calges
    assert a == {
        "id": 25,
        "key": "calges",
        "name_kor": "캘세더니 열쇠",
        "tier": "advanced",
        "combos": ["magic_engineering"],
        "effect_text": "관련된 속성 피해 +2/4/6/8",
        "max_level": 4,
        "scale_groups": [[2.0, 4.0, 6.0, 8.0]],
        "image": "https://img.sephiria.wiki/artifacts/calges_2.png",
    }

def test_normalize_no_ladder_uses_level_plus_one():
    # fire_bolt has no slash ladder but level=1 -> real max_level = level+1 = 2
    # (verified against the simulator oracle: badge "0 / 1", boosts to "1 / 1").
    raw = json.loads((FIX / "raw_artifacts_sample.json").read_text(encoding="utf-8"))
    a = normalize_artifact(raw[0])  # fire_bolt, level 1
    assert a["max_level"] == 2
    assert a["combos"] == ["yinggalbul"]

def test_normalize_ladder_max_level_equals_level_plus_one():
    # calges: ladder length 4 AND level 3 -> max_level 4 (the two agree for ladder items)
    raw = json.loads((FIX / "raw_artifacts_sample.json").read_text(encoding="utf-8"))
    a = normalize_artifact(raw[1])
    assert a["max_level"] == 4

def test_normalize_falls_back_to_ladder_when_level_missing():
    raw = {"id": 1, "value": "x", "label_kor": "x", "label_eng": "x", "tier": "common",
           "effect": {"sets": [], "content": "+1/2/3"}, "image": "x"}
    assert normalize_artifact(raw)["max_level"] == 3  # no 'level' -> ladder length
