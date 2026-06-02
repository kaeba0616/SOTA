import os
from sota.scrape.reconcile import RENAME_LOCAL_TO_WIKI

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
        "effects": raw.get("effects", []),
    }
