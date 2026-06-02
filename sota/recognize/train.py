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
        """Return one augmented copy of *image* using the per-folder strategy."""
        aug = image.copy()
        h, w = aug.shape[:2]

        # Rotation strategy: tablets get 360°; others get near-zero jitter.
        if folder_type == 'tablets':
            angle = np.random.choice([-180, -90, 0, 90, 180])
        else:
            angle = np.random.uniform(-1, 1)

        M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1)
        aug = cv2.warpAffine(aug, M, (w, h), borderMode=cv2.BORDER_REFLECT)

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

        # UI overlays matching the original training strategy
        if folder_type == 'artifacts' and np.random.rand() > 0.7:
            box_size = np.random.randint(15, 25)
            pt1 = (w - box_size, h - box_size)
            pt2 = (w, h)
            cv2.rectangle(aug, pt1, pt2, (20, 20, 20), -1)
            cv2.putText(aug, str(np.random.randint(1, 9)),
                        (w - box_size + 5, h - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        if folder_type == 'empty' and np.random.rand() > 0.4:
            font_scale = np.random.uniform(0.6, 1.0)
            text_x = np.random.randint(0, 10)
            text_y = np.random.randint(10, 20)
            cv2.putText(aug, "+1", (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 1)

        return aug.astype(np.uint8)

    dataset_dir = str(dataset_dir)
    data, label_list = [], []
    background_cache = {}

    # Discover class subdirectories
    folder_names = sorted(
        d for d in os.listdir(dataset_dir)
        if os.path.isdir(os.path.join(dataset_dir, d))
    )

    for folder_type in folder_names:
        folder_path = os.path.join(dataset_dir, folder_type)
        # Look for a matching slot background image relative to CNN/
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

            # Original image
            rgb = cv2.cvtColor(base_img, cv2.COLOR_BGR2RGB)
            resized = cv2.resize(rgb, (img_size, img_size))
            data.append(resized)
            label_list.append(label)

            # Augmented copies
            for _ in range(augment_count - 1):
                aug = _augment(base_img, folder_type)
                aug_rgb = cv2.cvtColor(aug, cv2.COLOR_BGR2RGB)
                aug_resized = cv2.resize(aug_rgb, (img_size, img_size))
                data.append(aug_resized)
                label_list.append(label)

    data = preprocess_input(np.array(data, dtype=np.float32))
    labels_arr = np.array(label_list)

    # Encode labels
    le = LabelEncoder()
    labels_enc = le.fit_transform(labels_arr)
    labels_onehot = to_categorical(labels_enc)

    # Persist class names immediately so they survive even if training is interrupted
    with open(out_classes, 'wb') as f:
        pickle.dump(le.classes_, f)

    # Train / validation split
    X_train, X_val, y_train, y_val = train_test_split(
        data, labels_onehot, test_size=0.2, random_state=42
    )

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
        X_train, y_train,
        epochs=epochs,
        batch_size=32,
        validation_data=(X_val, y_val),
        callbacks=[early_stop],
    )

    model.save(out_model)
