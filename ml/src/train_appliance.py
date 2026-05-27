"""
train_appliance.py — 1D-CNN for appliance classification from power waveforms.

Architecture:
    Input       : (50, 1) — 50-sample normalised power waveform
    Conv1D(32,3): relu + BatchNorm
    MaxPool1D(2)
    Conv1D(64,3): relu + BatchNorm
    Conv1D(64,3): relu
    GlobalAvgPool1D
    Dense(32, relu) → Dropout(0.3)
    Dense(N_CLASSES, softmax)

Classes (heuristic, override with measured labels):
    0: idle     1: lighting    2: fan    3: AC    4: other

Loss:   sparse_categorical_crossentropy
Metric: accuracy, top-2 accuracy
Target INT8 size: ~30 KB
"""

import argparse
import logging
import json
import numpy as np
from pathlib import Path
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

MODEL_NAME    = "model_appliance"
APPLIANCE_WIN = 50
N_CLASSES     = 5

APPLIANCE_NAMES = {0: "idle", 1: "lighting", 2: "fan", 3: "AC", 4: "other"}


def build_model(seq_len: int, n_classes: int) -> keras.Model:
    inp = keras.Input(shape=(seq_len, 1), name="power_waveform")

    x = layers.Conv1D(32, 3, padding="same", activation="relu", name="conv_1")(inp)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling1D(2)(x)

    x = layers.Conv1D(64, 3, padding="same", activation="relu", name="conv_2")(x)
    x = layers.BatchNormalization()(x)

    x = layers.Conv1D(64, 3, padding="same", activation="relu", name="conv_3")(x)

    x = layers.GlobalAveragePooling1D(name="gap")(x)

    x = layers.Dense(32, activation="relu", name="dense_1")(x)
    x = layers.Dropout(0.3)(x)

    out = layers.Dense(n_classes, activation="softmax", name="class_probs")(x)

    model = keras.Model(inputs=inp, outputs=out, name="appliance_cnn_1d")
    model.compile(
        optimizer=keras.optimizers.Adam(1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=[
            "accuracy",
            keras.metrics.SparseTopKCategoricalAccuracy(k=2, name="top2_acc"),
        ],
    )
    return model


def train(feat_dir: Path, model_dir: Path) -> None:
    model_dir.mkdir(parents=True, exist_ok=True)

    X = np.load(feat_dir / "appliance_X.npy").astype(np.float32)
    y = np.load(feat_dir / "appliance_y.npy").astype(np.int32)
    log.info("Loaded appliance X=%s  y=%s", X.shape, y.shape)

    n_classes = len(np.unique(y))
    log.info("Appliance classes present: %d", n_classes)

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )

    classes = np.unique(y_train)
    weights = compute_class_weight("balanced", classes=classes, y=y_train)
    class_weight = dict(zip(classes.tolist(), weights.tolist()))
    log.info("Class weights: %s", class_weight)

    model = build_model(seq_len=APPLIANCE_WIN, n_classes=n_classes)
    model.summary(print_fn=log.info)

    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=15,
            mode="max", restore_best_weights=True, verbose=1
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=7, verbose=1
        ),
        keras.callbacks.ModelCheckpoint(
            filepath=str(model_dir / f"{MODEL_NAME}_best.keras"),
            monitor="val_accuracy", mode="max", save_best_only=True
        ),
    ]

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=100,
        batch_size=128,
        class_weight=class_weight,
        callbacks=callbacks,
        verbose=2,
    )

    val_metrics = model.evaluate(X_val, y_val, verbose=0)
    results = dict(zip(model.metrics_names, val_metrics))
    log.info("Validation metrics: %s", results)

    keras_path = model_dir / f"{MODEL_NAME}.keras"
    model.save(keras_path)
    log.info("Keras model → %s", keras_path)

    meta = {
        "model": MODEL_NAME,
        "n_classes": n_classes,
        "class_names": APPLIANCE_NAMES,
        "seq_len": APPLIANCE_WIN,
        "epochs_trained": len(history.history["loss"]),
        "val_accuracy": float(results.get("accuracy", 0)),
        "val_top2_acc": float(results.get("top2_acc", 0)),
    }
    with open(model_dir / f"{MODEL_NAME}_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    log.info("Metadata → %s_meta.json", MODEL_NAME)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--feat_dir",  default="ml/data/features")
    ap.add_argument("--model_dir", default="ml/models")
    args = ap.parse_args()
    train(Path(args.feat_dir), Path(args.model_dir))
