"""Generate engine-snapshot golden cases for every tablet.

For each of the 54 tablets, this places the tablet alone on a full 6x6 grid,
runs the engine's level_deltas(), and records the result as a case in
tests/fixtures/tablet_snapshots.json.

IMPORTANT: these are ENGINE SELF-PREDICTIONS (regression snapshots), NOT
wiki-verified oracle values. test_tablet_snapshots.py asserts the engine
reproduces them (catches future regressions). To promote a case to a true
golden, confirm its expected_deltas against the wiki simulator and move it
into tests/fixtures/golden_deltas.json (verified by test_oracle_golden.py).

Run:  PYTHONPATH=. python3 tools/gen_tablet_snapshots.py
"""
import json
import pathlib

from sota.model.gamedata import load_game_data
from sota.model.grid import Grid
from sota.model.layout import Layout, TabletPlacement
from sota.evaluate.effects import level_deltas

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "fixtures" / "tablet_snapshots.json"
SLOT_COUNT = 36  # full 6x6 grid -> maximises on-grid effect cells

# Candidate anchor positions, tried in order; pick the one that yields the
# most non-zero deltas so each snapshot is a meaningful (non-empty) case.
ANCHORS = [(2, 2), (3, 3), (2, 3), (3, 2), (1, 1), (0, 0)]


def best_placement(key, gd, grid):
    best = None
    for (r, c) in ANCHORS:
        lay = Layout(slot_count=SLOT_COUNT,
                     tablets=[TabletPlacement(key, r, c, 0)],
                     artifacts=[])
        d = level_deltas(lay, grid, gd)
        nonzero = {k: v for k, v in d.items() if v != 0}
        if best is None or len(nonzero) > len(best[2]):
            best = ((r, c), d, nonzero)
        if len(nonzero) >= 1 and (r, c) == (2, 2):
            break  # prefer the canonical centre when it already works
    return best


def main():
    gd = load_game_data()
    grid = Grid(SLOT_COUNT)
    tablets = json.loads((ROOT / "sota" / "data" / "tablets.json").read_text("utf-8"))

    cases = []
    empties = []
    for t in tablets:
        key = t["key"]
        (r, c), deltas, nonzero = best_placement(key, gd, grid)
        expected = {f"{rr},{cc}": v for (rr, cc), v in sorted(nonzero.items())}
        # add two deliberately-zero cells for negative verification
        zeros = [(r, c)]  # the tablet's own cell
        far = (grid.rows - 1, grid.cols - 1)
        if far not in nonzero:
            zeros.append(far)
        for (zr, zc) in zeros:
            expected.setdefault(f"{zr},{zc}", 0)
        if not nonzero:
            empties.append(key)
        cases.append({
            "name": f"{key}_snapshot",
            "source": "engine-snapshot (UNVERIFIED — confirm against wiki simulator)",
            "tablet_name": t.get("name", ""),
            "effects": t.get("effects", []),
            "slot_count": SLOT_COUNT,
            "tablets": [{"key": key, "row": r, "col": c, "rotation": 0}],
            "expected_deltas": expected,
        })

    OUT.write_text(json.dumps(cases, indent=2, ensure_ascii=False) + "\n", "utf-8")
    print(f"wrote {len(cases)} cases -> {OUT.relative_to(ROOT)}")
    if empties:
        print(f"  {len(empties)} tablets produced no on-grid delta at tested anchors: {empties}")


if __name__ == "__main__":
    main()
