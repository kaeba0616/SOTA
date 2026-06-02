from dataclasses import dataclass
from sota.model.grid import Grid
from sota.evaluate.effects import level_deltas
from sota.evaluate.levels import effective_level
from sota.evaluate.special import is_special

STAGE_WEIGHT = 1000   # a combo stage dominates level tweaks

@dataclass(frozen=True)
class ScoreResult:
    score: int
    stages: int
    level_sum: int
    target_keys: list
    approximated: list

def combo_stages(combo, count) -> int:
    return sum(1 for t in combo["thresholds"] if t["count"] <= count)

def score_layout(lay, target_combo, gamedata) -> ScoreResult:
    grid = Grid(lay.slot_count)
    deltas = level_deltas(lay, grid, gamedata)
    target_keys, level_sum, approximated = [], 0, []
    for a in lay.artifacts:
        art = gamedata.artifacts.get(a.key)
        if art is None or target_combo not in art["combos"]:
            continue
        target_keys.append(a.key)
        level_sum += effective_level(art, deltas.get((a.row, a.col), 0))
        if is_special(art):
            approximated.append(a.key)
    combo = gamedata.combos[target_combo]
    stages = combo_stages(combo, len(target_keys))
    score = STAGE_WEIGHT * stages + level_sum
    return ScoreResult(score=score, stages=stages, level_sum=level_sum,
                       target_keys=target_keys, approximated=approximated)
