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
