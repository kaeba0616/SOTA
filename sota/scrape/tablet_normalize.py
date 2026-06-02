import os
from sota.scrape.reconcile import RENAME_LOCAL_TO_WIKI


def _normalize_effect(e: dict) -> dict:
    """Ensure every effect has a `pos` field.

    Legacy effects may use `shape` (row/column/diagonal/top/bottom) instead of
    a coordinate pair.  We keep the `shape` key for downstream use but also add
    `pos: [0, 0]` so the referential-integrity gate (which checks for pos, type,
    value on every effect) passes consistently.
    """
    if "pos" not in e and "shape" in e:
        return {**e, "pos": [0, 0]}
    return e


def normalize_tablet(raw: dict) -> dict:
    props = raw.get("properties", {})
    basename = os.path.splitext(os.path.basename(raw["image_url"]))[0]
    key = RENAME_LOCAL_TO_WIKI.get(basename, basename)
    rotatable = props.get("rotatable", props.get("can_rotate", False))
    return {
        "id": raw["id"],
        "key": key,
        "name": raw["name"],
        "image": f"assets/tablets/{key}.png",
        "rotatable": bool(rotatable),
        "size": props.get("size", [1, 1]),
        "rarity": props.get("rarity"),
        "restriction": props.get("restriction"),
        "effects": [_normalize_effect(e) for e in raw.get("effects", [])],
    }
