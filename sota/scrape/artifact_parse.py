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
    effect = raw.get("effect") or {}
    content = effect.get("content", "")
    parsed = parse_content(content)
    return {
        "id": raw["id"],
        "key": raw.get("value") or raw["label_eng"],
        "name_kor": raw["label_kor"],
        "tier": raw["tier"],
        "combos": list(effect.get("sets") or []),
        "effect_text": content,
        "max_level": parsed["max_level"],
        "scale_groups": parsed["scale_groups"],
        "image": raw["image"],
    }
