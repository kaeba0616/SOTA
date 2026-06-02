import pathlib
import pytest
pytest.importorskip("tensorflow")
from sota.recognize.classifier import Classifier

CNN = pathlib.Path(__file__).resolve().parents[1] / "CNN"


def test_classifier_loads_and_predicts():
    model_p = CNN / "sephiria_item_model.keras"
    classes_p = CNN / "classes.pickle"
    if not (model_p.exists() and classes_p.exists()):
        pytest.skip("no trained model present")
    import cv2, numpy as np
    clf = Classifier(model_p, classes_p)
    dummy = np.zeros((64, 64, 3), dtype=np.uint8)
    label, conf = clf.classify(dummy)
    assert isinstance(label, str) and 0.0 <= conf <= 1.0
