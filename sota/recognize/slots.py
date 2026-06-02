"""Inventory slot detection from game screenshots.

Ported from CNN/inven_test.py. Requires opencv-python (cv2).
"""

import cv2
import numpy as np

BORDER_COLOR_BGR = (52, 32, 36)


def non_max_suppression(boxes, overlap_thresh=0.3):
    if len(boxes) == 0:
        return []

    boxes = np.array(boxes)
    pick = []

    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 0] + boxes[:, 2]
    y2 = boxes[:, 1] + boxes[:, 3]

    area = boxes[:, 2] * boxes[:, 3]
    idxs = np.argsort(y1)

    while len(idxs) > 0:
        last = len(idxs) - 1
        i = idxs[last]
        pick.append(i)

        xx1 = np.maximum(x1[i], x1[idxs[:last]])
        yy1 = np.maximum(y1[i], y1[idxs[:last]])
        xx2 = np.minimum(x2[i], x2[idxs[:last]])
        yy2 = np.minimum(y2[i], y2[idxs[:last]])

        w = np.maximum(0, xx2 - xx1)
        h = np.maximum(0, yy2 - yy1)

        overlap = (w * h) / area[idxs[:last]]

        idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > overlap_thresh)[0])))

    return boxes[pick].tolist()


def find_slots(image_bgr):
    """Detect inventory slot bounding boxes in a BGR screenshot.

    Returns a list of (x, y, w, h) tuples sorted in row-major order.
    Uses adaptive sizing based on image dimensions, a hybrid border+invert
    contour detection strategy (methods A and B), multiscale fallback, and
    NMS to de-duplicate candidates.
    """
    image = image_bgr
    img_h, img_w = image.shape[:2]

    # Adaptive slot size estimate: slots are roughly 8% of image width
    estimated_slot_size = img_w * 0.08

    min_size = int(estimated_slot_size * 0.7)
    max_size = int(estimated_slot_size * 1.5)

    # Border colour mask
    tolerance = 15
    lower = np.array([max(0, c - tolerance) for c in BORDER_COLOR_BGR])
    upper = np.array([min(255, c + tolerance) for c in BORDER_COLOR_BGR])

    mask = cv2.inRange(image, lower, upper)

    # Adaptive kernel size
    kernel_size = max(3, int(img_w / 500))
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

    candidates = []

    # Method A: edge-based contours on the border mask
    edges = cv2.Canny(mask, 50, 150)
    contours_A, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours_A:
        x, y, w, h = cv2.boundingRect(cnt)
        ar = w / float(h) if h > 0 else 0
        if min_size < w < max_size and min_size < h < max_size and 0.75 < ar < 1.25:
            candidates.append([x, y, w, h])

    # Method B: inverted mask contours
    mask_inv = cv2.bitwise_not(mask)
    contours_B, _ = cv2.findContours(mask_inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours_B:
        x, y, w, h = cv2.boundingRect(cnt)
        ar = w / float(h) if h > 0 else 0
        if min_size < w < max_size and min_size < h < max_size and 0.75 < ar < 1.25:
            candidates.append([x, y, w, h])

    # Multiscale fallback when no candidates found
    if len(candidates) == 0:
        for scale_factor in [0.6, 0.8, 1.0, 1.2, 1.5]:
            min_s = int(estimated_slot_size * scale_factor * 0.7)
            max_s = int(estimated_slot_size * scale_factor * 1.5)

            temp_candidates = []
            for cnt in contours_A:
                x, y, w, h = cv2.boundingRect(cnt)
                if min_s < w < max_s and min_s < h < max_s:
                    temp_candidates.append([x, y, w, h])

            if len(temp_candidates) > 0:
                candidates = temp_candidates
                break

        if len(candidates) == 0:
            return []

    # NMS de-duplication
    final_slots = non_max_suppression(candidates, overlap_thresh=0.3)

    if isinstance(final_slots, np.ndarray):
        final_slots = final_slots.tolist()

    # Row-major sort using adaptive row gap (20% of estimated slot size)
    row_gap = max(10, int(estimated_slot_size * 0.2))
    final_slots = sorted(final_slots, key=lambda s: (s[1] // row_gap, s[0]))

    return [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in final_slots]
