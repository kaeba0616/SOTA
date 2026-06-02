# canonical key = wiki slab id; value = the basename currently used in root tablet.json image_url
RENAME_LOCAL_TO_WIKI = {
    "arrival": "advent",
    "competition": "compete",
    "goodness": "linear",
    "three_heads": "triceps",
    "fusion": "unity",
    "desire": "yearning",
    "encouragement": "home_town",  # 고양 — rename, not stale
}
# slabs present in-game (54) but absent from tablet.json -> authored from wiki oracle
MISSING_TABLET_KEYS = {
    "courage": "용기",
    "honor": "명예",
    "hospitality": "환대",
    "peace": "평화",
}
# in tablet.json but not in-game after rename -> none remain
STALE_TABLET_KEYS = set()


def reconcile(tablet_keys: set[str], slab_keys: set[str]) -> dict:
    """Classify normalized tablet keys against in-game slab keys."""
    return {
        "matched": tablet_keys & slab_keys,
        "missing": slab_keys - tablet_keys,   # in game, not authored yet
        "stale": tablet_keys - slab_keys,     # authored, not in game (removed)
    }
