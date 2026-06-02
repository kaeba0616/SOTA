from sota.model.pool import ItemPool
from sota.recognize.keymap import label_to_item

def pool_from_labels(labels, gamedata, min_conf=0.5):
    """labels: list of (label, confidence). Returns (ItemPool, low_confidence_list).
    Drops 'empty'/unknown; items below min_conf are excluded AND reported in low list."""
    tablets, artifacts, low = [], [], []
    for label, conf in labels:
        item = label_to_item(label, gamedata)
        if item is None:
            continue
        if conf < min_conf:
            low.append((label, conf))
            continue
        kind, key = item
        (tablets if kind == "tablet" else artifacts).append(key)
    return ItemPool(tablets=tablets, artifacts=artifacts), low
