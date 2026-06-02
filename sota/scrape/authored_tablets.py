"""Effect geometry for slabs absent from the legacy tablet.json, read from the
wiki slab effect-grid tooltips (/large) on 2026-06-02 and verified against known
tablets. Coordinate convention matches tablet.json: pos=[dx, dy], dx right-positive,
dy up-positive; value is the per-cell level delta; type 'level_add'."""

AUTHORED = [
    {"key": "courage", "name": "용기", "rotatable": True, "size": [1, 1],
     "rarity": None, "restriction": None, "effects": [
        {"pos": [-2, 2], "type": "level_add", "value": 1},
        {"pos": [-1, 1], "type": "level_add", "value": 1},
        {"pos": [1, 1], "type": "level_add", "value": 2},
        {"pos": [-1, -1], "type": "level_add", "value": 2},
        {"pos": [1, -1], "type": "level_add", "value": 1},
        {"pos": [2, -2], "type": "level_add", "value": 1}]},
    {"key": "honor", "name": "명예", "rotatable": True, "size": [1, 1],
     "rarity": None, "restriction": None, "effects": [
        {"pos": [-1, 2], "type": "level_add", "value": 1},
        {"pos": [0, 1], "type": "level_add", "value": 2}]},
    {"key": "hospitality", "name": "환대", "rotatable": False, "size": [1, 1],
     "rarity": None, "restriction": None, "effects": [
        {"pos": [0, 1], "type": "level_add", "value": 1},
        {"pos": [-1, 0], "type": "level_add", "value": 2}]},
    {"key": "peace", "name": "평화", "rotatable": True, "size": [1, 1],
     "rarity": None, "restriction": None, "effects": [
        {"pos": [-1, 0], "type": "level_add", "value": 3},
        {"pos": [1, 0], "type": "level_add", "value": 3}]},
]
