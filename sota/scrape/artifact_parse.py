import re

_LADDER = re.compile(r"\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)+")

def parse_content(content: str) -> dict:
    """Parse an artifact effect text into max_level + numeric ladders.

    max_level = longest slash-separated numeric ladder length, min 1.
    """
    groups = []
    for match in _LADDER.finditer(content or ""):
        groups.append([float(x) for x in match.group(0).split("/")])
    max_level = max((len(g) for g in groups), default=1)
    return {"max_level": max_level, "scale_groups": groups}


def normalize_artifact(raw: dict) -> dict:
    """Normalize a raw wiki artifact object.

    max_level is the artifact's real level cap, verified against the simulator
    oracle (2026-06-02): an artifact starts at level 1 and a tablet boost of B
    raises it to level 1+B, clamped at `max_level`. The wiki `level` field is the
    maximum boost (the badge's "X / Y" second number Y), so max_level = level + 1.
    The slash-ladder length only equals this for ladder artifacts; for [고유]
    (spell/summon) artifacts the ladder is absent or partial, so `level` is the
    authority. scale_groups (the numeric ladders) are kept for value computation.
    """
    effect = raw.get("effect") or {}
    content = effect.get("content", "")
    parsed = parse_content(content)
    base = raw.get("level")
    max_level = base + 1 if isinstance(base, int) else parsed["max_level"]
    return {
        "id": raw["id"],
        "key": raw.get("value") or raw["label_eng"],
        "name_kor": raw["label_kor"],
        "tier": raw["tier"],
        "combos": list(effect.get("sets") or []),
        "effect_text": content,
        "max_level": max_level,
        "scale_groups": parsed["scale_groups"],
        "image": raw["image"],
    }
