import pytest
cv2 = pytest.importorskip("cv2")
import pathlib
from sota.recognize.slots import find_slots

CNN = pathlib.Path(__file__).resolve().parents[1] / "CNN"


@pytest.mark.parametrize("img", ["test1.png", "test2.png", "test3.png"])
def test_detects_some_slots(img):
    frame = cv2.imread(str(CNN / img))
    if frame is None:
        pytest.skip(f"{img} not present")
    boxes = find_slots(frame)
    assert isinstance(boxes, list)
    assert len(boxes) >= 1
    for (x, y, w, h) in boxes:
        assert w > 0 and h > 0
    ys = [b[1] for b in boxes]
    assert ys == sorted(ys) or len(boxes) < 3
