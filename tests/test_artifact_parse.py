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

def test_normalize_unique_effect_level_one():
    raw = json.loads((FIX / "raw_artifacts_sample.json").read_text(encoding="utf-8"))
    a = normalize_artifact(raw[0])  # fire_bolt
    assert a["max_level"] == 1
    assert a["combos"] == ["yinggalbul"]
