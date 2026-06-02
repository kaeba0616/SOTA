# Markers in effect_text indicating global / positional / conditional behavior
# that the v1 level-based model approximates (and flags in the score breakdown).
SPECIAL_MARKERS = (
    "석판", "인벤토리", "가로줄", "세로줄", "위치", "양쪽", "줄에", "개수만큼", "개당",
)

def is_special(artifact) -> bool:
    text = artifact.get("effect_text", "")
    return any(m in text for m in SPECIAL_MARKERS)
