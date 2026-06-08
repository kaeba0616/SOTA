import base64
import io

import numpy as np

from sota.model.pool import ItemPool
from sota.solve.ga import solve
from sota.render.summary import build_summary
from sota.render.grid_image import render_layout
from sota.recognize.slots import find_slots
from sota.recognize.keymap import label_to_item


def solve_build(*, tablets, artifacts, combo, slots, seed, generations,
                pop_size, gamedata, root):
    """Run the GA solver and return build_summary(...) plus a base64 PNG.

    Raises ValueError (-> HTTP 400) for unknown combo/keys or bad slot count.
    generations/pop_size are clamped to a safe maximum to prevent runaway.
    """
    if not (1 <= slots <= 60):
        raise ValueError(f"slots out of range: {slots} (expected 1..60)")
    bad_t = [k for k in tablets if k not in gamedata.tablets]
    bad_a = [k for k in artifacts if k not in gamedata.artifacts]
    if bad_t or bad_a:
        raise ValueError(f"unknown keys: tablets={bad_t} artifacts={bad_a}")
    if combo not in gamedata.combos:
        raise ValueError(f"unknown combo: {combo}")

    generations = max(1, min(int(generations), 300))
    pop_size = max(1, min(int(pop_size), 300))

    pool = ItemPool(tablets=list(tablets), artifacts=list(artifacts))
    result = solve(pool, combo, slot_count=slots, gamedata=gamedata,
                   seed=seed, generations=generations, pop_size=pop_size)
    summary = build_summary(result.layout, combo, gamedata)

    img = render_layout(result.layout, combo, gamedata, root)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    summary["image_base64"] = base64.b64encode(buf.getvalue()).decode("ascii")
    return summary


def recognize_image(image_bytes, classifier, gamedata):
    """Decode an uploaded screenshot, detect slots, classify each.

    Returns a list of dicts in row-major order:
      {slot, row, col, type, key, confidence}
    type is the keymap kind ("tablet"/"artifact") or "empty" for empty/unknown.
    Raises ValueError (-> HTTP 400) if the bytes are not a decodable image.
    """
    import cv2
    frame = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("could not decode image")
    boxes = sorted(find_slots(frame), key=lambda b: (round(b[1] / 100), b[0]))
    items = []
    for i, (x, y, w, h) in enumerate(boxes):
        roi = frame[y:y + h, x:x + w]
        if roi.size == 0:
            continue
        key, conf = classifier.classify(roi)
        item = label_to_item(key, gamedata)
        typ = "empty" if item is None else item[0]
        items.append({"slot": i, "row": i // 6, "col": i % 6,
                      "type": typ, "key": key, "confidence": float(conf)})
    return items
