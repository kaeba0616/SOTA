import json, pathlib
from dataclasses import dataclass

_DATA = pathlib.Path(__file__).resolve().parents[1] / "data"

@dataclass(frozen=True)
class GameData:
    artifacts: dict
    tablets: dict
    combos: dict

def _load(name):
    return json.loads((_DATA / name).read_text(encoding="utf-8"))

def load_game_data() -> GameData:
    return GameData(
        artifacts={a["key"]: a for a in _load("artifacts.json")},
        tablets={t["key"]: t for t in _load("tablets.json")},
        combos={c["key"]: c for c in _load("combos.json")},
    )
