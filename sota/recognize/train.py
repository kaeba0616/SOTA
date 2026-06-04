"""Training entrypoint for the inventory-slot item classifier.

All heavy imports (tensorflow, sklearn, cv2) are deferred inside the
function body so that importing this module never crashes when those
packages are absent.

Typical run commands after building the canonical dataset::

    python3 -c "from sota.recognize.dataset import build_canonical_dataset as b; import pathlib; b(pathlib.Path('.'), pathlib.Path('build/dataset'))"
    python3 -c "from sota.recognize.train import train_model as t; t('build/dataset','CNN/sephiria_item_model.keras','CNN/classes.pickle')"
"""


def train_model(
    dataset_dir,
    out_model,
    out_classes,
    img_size=128,
    augment_count=150,
    epochs=30,
):
    """Train a MobileNetV2 transfer-learning classifier and save the result.

    Parameters
    ----------
    dataset_dir:
        Path to a directory whose subdirectories are class names (e.g.
        ``artifacts/``, ``tablets/``, ``empty/``).  Matches the layout
        produced by ``sota.recognize.dataset.build_canonical_dataset``.
    out_model:
        Destination ``.keras`` file for the saved Keras model.
    out_classes:
        Destination ``.pickle`` file for the list of class-name strings.
    img_size:
        Square side length (pixels) used for training and inference (128).
    augment_count:
        How many images to produce per source image (150 by default).
    epochs:
        Maximum training epochs (early-stopping may halt sooner).
    """
    import os
    import pickle
    import numpy as np
    import cv2
    import tensorflow as tf
    from tensorflow.keras import layers, models, optimizers
    from tensorflow.keras.applications import MobileNetV2
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
    from tensorflow.keras.callbacks import EarlyStopping
    from tensorflow.keras.utils import to_categorical
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder

    VALID_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp')

    # Slot-type background colours used when the source PNG has transparency.
    # Keys match subdirectory names; fallback grey otherwise.
    BG_COLORS = {
        'artifacts': (59, 58, 73),
        'tablets':   (59, 59, 88),
        'empty':     (98, 49, 68),
    }

    def _load_background(bg_path, target_size, folder_type):
        default_color = BG_COLORS.get(folder_type, (60, 60, 60))
        if not os.path.exists(bg_path):
            return np.full((target_size, target_size, 3), default_color, dtype=np.uint8)
        bg = cv2.imread(bg_path, cv2.IMREAD_COLOR)
        if bg is None:
            return np.full((target_size, target_size, 3), default_color, dtype=np.uint8)
        return cv2.resize(bg, (target_size, target_size))

    def _augment(image, folder_type):
        """Return one augmented copy of *image* using the per-folder strategy.

        Calibrated to the REAL in-game slot rendering observed in the test
        screenshots (CNN/test*.png), so the synthetic training distribution
        matches inference:
          * the canonical icon occupies only ~72-96% of the slot (padding +
            a frame), not the whole frame;
          * artifacts carry a top-RIGHT ``X/Y`` level badge (green or white),
            NOT a bottom-right single digit;
          * tablets carry a small red top-LEFT index digit and a 90° rotation;
          * slots have a faint bevel border.
        """
        bg_color = BG_COLORS.get(folder_type, (60, 60, 60))
        aug = image.copy()
        h, w = aug.shape[:2]

        # Rotation strategy: tablets get 360°; others get near-zero jitter.
        if folder_type == 'tablets':
            angle = np.random.choice([-180, -90, 0, 90, 180])
        else:
            angle = np.random.uniform(-3, 3)

        M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1)
        aug = cv2.warpAffine(aug, M, (w, h), borderMode=cv2.BORDER_REFLECT)

        # Scale + pad: real icons sit inside the slot with margin, on slot bg.
        if np.random.rand() < 0.85:
            s = np.random.uniform(0.72, 0.96)
            nh, nw = max(1, int(h * s)), max(1, int(w * s))
            small = cv2.resize(aug, (nw, nh), interpolation=cv2.INTER_AREA)
            canvas = np.full((h, w, 3), bg_color, np.uint8)
            oy = np.random.randint(0, h - nh + 1)
            ox = np.random.randint(0, w - nw + 1)
            canvas[oy:oy + nh, ox:ox + nw] = small
            aug = canvas

        # Brightness jitter
        value = np.random.randint(-30, 30)
        aug = np.clip(aug.astype(np.int16) + value, 0, 255).astype(np.uint8)

        # Stochastic quality degradation
        if np.random.rand() > 0.5:
            deg_type = np.random.choice(['blur', 'downsample', 'combined'])
            if deg_type == 'blur':
                aug = cv2.GaussianBlur(aug, (3, 3), 0)
            elif deg_type == 'downsample':
                scale = np.random.uniform(0.7, 0.9)
                sh, sw = int(h * scale), int(w * scale)
                small = cv2.resize(aug, (sw, sh), interpolation=cv2.INTER_AREA)
                aug = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
            else:  # combined
                scale = np.random.uniform(0.7, 0.9)
                sh, sw = int(h * scale), int(w * scale)
                small = cv2.resize(aug, (sw, sh), interpolation=cv2.INTER_AREA)
                aug = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
                if np.random.rand() > 0.5:
                    aug = cv2.GaussianBlur(aug, (3, 3), 0)

        # Faint bevel border around the slot (lighter than the bg).
        if np.random.rand() < 0.5:
            bc = tuple(min(255, int(c * 1.5) + 10) for c in bg_color)
            cv2.rectangle(aug, (0, 0), (w - 1, h - 1), bc, 1)

        # Top-RIGHT "X/Y" level badge on artifacts (green, sometimes white),
        # on a dark pill — matches the real game HUD.
        if folder_type == 'artifacts' and np.random.rand() < 0.78:
            x = int(np.random.randint(1, 9))
            y = int(np.random.randint(x, 10))
            txt = f'{x}/{y}'
            fs = np.random.uniform(0.38, 0.52)
            (tw, th), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, fs, 1)
            bx, by = w - tw - 2, th + 3
            cv2.rectangle(aug, (bx - 2, by - th - 2), (bx + tw + 2, by + 3),
                          (22, 26, 22), -1)
            col = (120, 240, 120) if np.random.rand() < 0.7 else (245, 245, 245)
            cv2.putText(aug, txt, (bx, by), cv2.FONT_HERSHEY_SIMPLEX, fs, col,
                        1, cv2.LINE_AA)

        # Tablets: small red top-LEFT index digit.
        if folder_type == 'tablets' and np.random.rand() < 0.7:
            d = str(np.random.randint(1, 6))
            cv2.putText(aug, d, (2, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (50, 50, 225), 2, cv2.LINE_AA)

        # Empty slots: occasional "+N" hint text.
        if folder_type == 'empty' and np.random.rand() > 0.4:
            font_scale = np.random.uniform(0.6, 1.0)
            text_x = np.random.randint(0, 10)
            text_y = np.random.randint(10, 20)
            cv2.putText(aug, f"+{np.random.randint(1, 4)}", (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 1)

        return aug.astype(np.uint8)

    dataset_dir = str(dataset_dir)
    base_imgs, base_folders, label_list = [], [], []
    background_cache = {}

    # Discover class subdirectories
    folder_names = sorted(
        d for d in os.listdir(dataset_dir)
        if os.path.isdir(os.path.join(dataset_dir, d))
    )

    # Load ONLY the canonical source icon per class (composited onto its slot
    # background).  Augmentation happens lazily per-batch in the Sequence below,
    # so we never hold the full ~N*augment_count image set in RAM (that caused
    # the OOM kill on this 9.7 GiB box).
    for folder_type in folder_names:
        folder_path = os.path.join(dataset_dir, folder_type)
        bg_path = os.path.join(
            os.path.dirname(os.path.abspath(str(out_model))),
            f"slot_{folder_type}.png",
        )

        for filename in os.listdir(folder_path):
            if not filename.lower().endswith(VALID_EXTENSIONS):
                continue
            label = os.path.splitext(filename)[0]
            img_path = os.path.join(folder_path, filename)
            img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
            if img is None:
                continue

            # Composite transparent images onto slot background
            if img.ndim == 3 and img.shape[2] == 4:
                if bg_path not in background_cache:
                    background_cache[bg_path] = _load_background(
                        bg_path, img.shape[0], folder_type
                    )
                bg = cv2.resize(
                    background_cache[bg_path], (img.shape[1], img.shape[0])
                )
                alpha_f = img[:, :, 3:4] / 255.0
                base_img = (img[:, :, :3] * alpha_f + bg * (1 - alpha_f)).astype(np.uint8)
            else:
                base_img = img

            base_imgs.append(base_img)        # uint8 BGR, native size (~tiny)
            base_folders.append(folder_type)
            label_list.append(label)

    n_base = len(base_imgs)
    labels_arr = np.array(label_list)

    # Encode labels
    le = LabelEncoder()
    labels_enc = le.fit_transform(labels_arr)
    labels_onehot = to_categorical(labels_enc).astype(np.float32)

    # Persist class names immediately so they survive even if training is interrupted
    with open(out_classes, 'wb') as f:
        pickle.dump(le.classes_, f)

    # Each class has exactly ONE source icon, so we cannot split base images into
    # train/val per class.  Instead we split over the augmented *copies*: a flat
    # index f maps to (base = f % n_base, copy = f // n_base); copy 0 is the
    # pristine original.  Holding out 20% of copies measures robustness to the
    # render variation we expect at inference (same items, different lighting/UI).
    total = n_base * augment_count
    rng = np.random.RandomState(42)
    flat = rng.permutation(total)
    n_val = max(1, int(total * 0.2))
    val_flat = flat[:n_val]
    train_flat = flat[n_val:]

    class _AugSeq(tf.keras.utils.Sequence):
        def __init__(self, flat_indices, batch_size, training):
            super().__init__()
            self.flat = flat_indices
            self.bs = batch_size
            self.training = training

        def __len__(self):
            return int(np.ceil(len(self.flat) / self.bs))

        def __getitem__(self, idx):
            chunk = self.flat[idx * self.bs:(idx + 1) * self.bs]
            X = np.empty((len(chunk), img_size, img_size, 3), np.float32)
            Y = np.empty((len(chunk), labels_onehot.shape[1]), np.float32)
            for i, f in enumerate(chunk):
                b = int(f % n_base)
                copy_idx = int(f // n_base)
                img = base_imgs[b]
                if copy_idx > 0:  # copy 0 stays pristine
                    img = _augment(img, base_folders[b])
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                rgb = cv2.resize(rgb, (img_size, img_size))
                X[i] = rgb
                Y[i] = labels_onehot[b]
            return preprocess_input(X), Y

    train_seq = _AugSeq(train_flat, 32, True)
    val_seq = _AugSeq(val_flat, 32, False)

    # MobileNetV2 transfer model
    base_model = MobileNetV2(
        weights='imagenet', include_top=False,
        input_shape=(img_size, img_size, 3), alpha=1.0
    )
    base_model.trainable = False

    model = models.Sequential([
        layers.Input(shape=(img_size, img_size, 3)),
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dense(256, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(len(le.classes_), activation='softmax', dtype='float32'),
    ])

    model.compile(
        optimizer=optimizers.Adam(learning_rate=0.0001),
        loss='categorical_crossentropy',
        metrics=['accuracy'],
    )

    early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

    model.fit(
        train_seq,
        epochs=epochs,
        validation_data=val_seq,
        callbacks=[early_stop],
    )

    model.save(out_model)
