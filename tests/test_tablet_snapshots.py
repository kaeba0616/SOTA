"""Regression snapshots for all 54 tablets' level-delta computation.

Each case in tests/fixtures/tablet_snapshots.json places one tablet on a full
6x6 grid and records the engine's level_deltas() output. This test asserts the
engine still reproduces those values, so any accidental change to the effect
engine is caught for EVERY tablet.

These are engine self-predictions, NOT wiki-verified oracle values — they lock
*current behaviour*, not correctness. Regenerate after an intentional engine
change with:  PYTHONPATH=. python3 tools/gen_tablet_snapshots.py
To verify a tablet against the simulator, promote its case into
tests/fixtures/golden_deltas.json (asserted by test_oracle_golden.py).
"""
import json
import pathlib

import pytest

from sota.model.gamedata import load_game_data
from sota.model.grid import Grid
from sota.model.layout import Layout, TabletPlacement
from sota.evaluate.effects import level_deltas

GD = load_game_data()
FIX = pathlib.Path(__file__).parent / "fixtures" / "tablet_snapshots.json"


def _cases():
    if not FIX.exists():
        return []
    return json.loads(FIX.read_text(encoding="utf-8"))


def test_every_tablet_has_a_snapshot():
    keys = {c["tablets"][0]["key"] for c in _cases()}
    tablets = json.loads(
        (pathlib.Path(__file__).resolve().parents[1] / "sota" / "data" / "tablets.json")
        .read_text(encoding="utf-8")
    )
    expected = {t["key"] for t in tablets}
    missing = expected - keys
    assert not missing, f"tablets without a snapshot: {missing}"


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c["name"])
def test_engine_reproduces_tablet_snapshot(case):
    lay = Layout(
        slot_count=case["slot_count"],
        tablets=[TabletPlacement(**t) for t in case["tablets"]],
        artifacts=[],
    )
    grid = Grid(lay.slot_count)
    deltas = level_deltas(lay, grid, GD)
    for cell_str, expected in case["expected_deltas"].items():
        r, c = map(int, cell_str.split(","))
        assert deltas.get((r, c), 0) == expected, (
            f"{case['name']}: cell {cell_str} expected {expected}, "
            f"got {deltas.get((r, c), 0)}"
        )
