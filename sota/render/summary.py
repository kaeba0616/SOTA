from sota.model.grid import Grid
from sota.evaluate.effects import level_deltas
from sota.evaluate.levels import effective_level
from sota.evaluate.score import score_layout

def build_summary(layout, target_combo, gamedata) -> dict:
    grid = Grid(layout.slot_count)
    deltas = level_deltas(layout, grid, gamedata)
    res = score_layout(layout, target_combo, gamedata)
    targets = []
    for a in layout.artifacts:
        art = gamedata.artifacts.get(a.key)
        if art is None or target_combo not in art["combos"]:
            continue
        targets.append({
            "key": a.key,
            "name": art["name_kor"],
            "cell": [a.row, a.col],
            "level": effective_level(art, deltas.get((a.row, a.col), 0)),
            "max_level": art["max_level"],
            "special": a.key in res.approximated,
        })
    return {
        "combo": target_combo,
        "score": res.score,
        "stages": res.stages,
        "level_sum": res.level_sum,
        "targets": targets,
        "tablets": [{"key": t.key, "cell": [t.row, t.col], "rotation": t.rotation}
                    for t in layout.tablets],
        "approximated": list(res.approximated),
    }

def format_summary(s: dict) -> str:
    lines = [
        f"combo: {s['combo']}",
        f"score: {s['score']}  (stages {s['stages']} x 1000 + levels {s['level_sum']})",
        f"target artifacts ({len(s['targets'])}):",
    ]
    for t in s["targets"]:
        mark = " *approx" if t["special"] else ""
        lines.append(f"  - {t['key']} @ {t['cell']}  Lv {t['level']}/{t['max_level']}{mark}")
    lines.append(f"tablets ({len(s['tablets'])}): " + ", ".join(
        f"{t['key']}@{t['cell']}" for t in s["tablets"]))
    if s["approximated"]:
        lines.append("approximated (special, level-only): " + ", ".join(s["approximated"]))
    return "\n".join(lines)
