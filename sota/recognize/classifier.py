"""Keras-based item classifier for inventory slot ROIs.

Heavy imports (tensorflow, cv2) are deferred into method bodies so that
importing this module does not crash when those packages are absent.
"""

import pickle
import numpy as np

IMG_SIZE = 128


class Classifier:
    def __init__(self, model_path, classes_path):
        from tensorflow.keras.models import load_model
        self.model = load_model(model_path)
        with open(classes_path, "rb") as f:
            self.class_names = pickle.load(f)

    def classify(self, roi_bgr):
        """Classify one slot ROI (BGR ndarray) -> (label, confidence)."""
        import cv2
        from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
        rgb = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_NEAREST)
        x = preprocess_input(resized.astype(np.float32))[None, ...]
        pred = self.model.predict(x, verbose=0)[0]
        i = int(np.argmax(pred))
        return self.class_names[i], float(pred[i])
