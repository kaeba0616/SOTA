"""Orchestrates slot detection + classification for a full screenshot."""

from dataclasses import dataclass
from sota.recognize.slots import find_slots


@dataclass(frozen=True)
class RecognitionResult:
    labels: list


def recognize_screenshot(path, classifier):
    """Detect slots and classify each -> RecognitionResult(labels=[(label,conf)])."""
    import cv2
    frame = cv2.imread(str(path))
    if frame is None:
        raise FileNotFoundError(path)
    labels = []
    for (x, y, w, h) in find_slots(frame):
        roi = frame[y:y + h, x:x + w]
        if roi.size == 0:
            continue
        labels.append(classifier.classify(roi))
    return RecognitionResult(labels=labels)
