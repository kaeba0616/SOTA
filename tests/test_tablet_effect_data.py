"""Pin specific tablet point-effects to the authoritative wiki values.

Extracted from the sephiria.wiki simulator bundle's effect map `r` (2026-06-08)
and converted to our convention: our pos == [dx_wiki, -dy_wiki], value unchanged.
These two tablets had transcription errors in the legacy/authored data:
  - tide: one effect's dx sign was flipped ([-1,0] -> should be [1,0])
  - courage: the outermost diagonal cell [-3,3] was missing
"""
import json
import pathlib

DATA = pathlib.Path(__file__).resolve().parents[1] / "sota" / "data" / "tablets.json"
TABLETS = {t["key"]: t for t in json.loads(DATA.read_text(encoding="utf-8"))}

# Wiki-verified point effects as {(dx, dy, value), ...} in our convention.
WIKI = {
    "tide": {(1, 1, 2), (0, 1, -1), (1, 0, -1)},
    "courage": {(-3, 3, 1), (-2, 2, 1), (-1, 1, 1), (1, -1, 1),
                (2, -2, 1), (1, 1, 2), (-1, -1, 2)},
}


def _pointset(key):
    return {(e["pos"][0], e["pos"][1], e.get("value", 1))
            for e in TABLETS[key]["effects"]
            if e.get("type") == "level_add" and "pos" in e}


def test_tide_matches_wiki():
    assert _pointset("tide") == WIKI["tide"]


def test_courage_matches_wiki():
    assert _pointset("courage") == WIKI["courage"]
