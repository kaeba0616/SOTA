"""Golden tests: the engine's tablet-boost (level delta) computation must reproduce
values read from the wiki simulator, which displays each placed artifact's tablet
boost as the first number of its badge.

Scope: these lock the *delta* (tablet boost) computation and the coordinate
convention — the optimizer-critical quantity. The artifact base level (the badge's
second number) and exact clamp semantics are an open calibration item documented in
docs/CALIBRATION.md; they are NOT asserted here.
"""
import json
import pathlib

import pytest

from sota.model.gamedata import load_game_data
from sota.model.grid import Grid
from sota.model.layout import Layout, TabletPlacement
from sota.evaluate.effects import level_deltas

GD = load_game_data()
FIX = pathlib.Path(__file__).parent / "fixtures" / "golden_deltas.json"


def _cases():
    if not FIX.exists():
        return []
    return json.loads(FIX.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c["name"])
def test_engine_deltas_match_simulator(case):
    lay = Layout(
        slot_count=case["slot_count"],
        tablets=[TabletPlacement(**t) for t in case["tablets"]],
        artifacts=[],
    )
    grid = Grid(lay.slot_count)
    deltas = level_deltas(lay, grid, GD)
    for cell_str, expected in case["expected_deltas"].items():
        r, c = map(int, cell_str.split(","))
        got = deltas.get((r, c), 0)
        assert got == expected, f"{case['name']} @ {cell_str}: got {got}, expected {expected}"
