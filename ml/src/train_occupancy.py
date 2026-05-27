"""
train_occupancy.py — Dense NN (3 layers) for occupancy prediction.

Architecture:
    Input  : (9,) — power_w, motion, temperature, humidity,
                    hour_sin, hour_cos, dow_sin, dow_cos, is_weekend
    Hidden : Dense(32, relu) → BatchNorm → Dropout(0.3)
    Hidden : Dense(16, relu) → Dropout(0.2)
    Output : Dense(1, sigmoid) — occupancy probability

Loss:   binary_crossentropy
Metric: AUC, accuracy
Target INT8 size: ~15 KB
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

MODEL_NAME = "model_occupancy"


def build_model(n_features: int) -> keras.Model:
    inp = keras.Input(shape=(n_features,), name="sensor_features")

    x = layers.Dense(32, activation="relu", name="dense_1")(inp)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.3)(x)

    x = layers.Dense(16, activation="relu", name="dense_2")(x)
    x = layers.Dropout(0.2)(x)

    out = layers.Dense(1, activation="sigmoid", name="occupancy_prob")(x)

    model = keras.Model(inputs=inp, outputs=out, name="occupancy_nn")
    model.compile(
        optimizer=keras.optimizers.Adam(1e-3),
        loss="binary_crossentropy",
        metrics=[
            keras.metrics.AUC(name="auc"),
            keras.metrics.BinaryAccuracy(name="accuracy"),
        ],
    )
    return model


def train(feat_dir: Path, model_dir: Path) -> None:
    model_dir.mkdir(parents=True, exist_ok=True)

    X = np.load(feat_dir / "occupancy_X.npy").astype(np.float32)
    y = np.load(feat_dir / "occupancy_y.npy").astype(np.float32)
    log.info("Loaded occupancy X=%s  y=%s  pos_rate=%.2f%%",
             X.shape, y.shape, 100 * y.mean())

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y.astype(int)
    )

    # Handle class imbalance
    classes = np.unique(y_train.astype(int))
    weights = compute_class_weight("balanced", classes=classes,
                                   y=y_train.astype(int))
    class_weight = dict(zip(classes, weights))
    log.info("Class weights: %s", class_weight)

    model = build_model(n_features=X.shape[1])
    model.summary(print_fn=log.info)

    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_auc", patience=10,
            mode="max", restore_best_weights=True, verbose=1
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=5, verbose=1
        ),
        keras.callbacks.ModelCheckpoint(
            filepath=str(model_dir / f"{MODEL_NAME}_best.keras"),
            monitor="val_auc", mode="max", save_best_only=True
        ),
    ]

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=100,
        batch_size=256,
        class_weight=class_weight,
        callbacks=callbacks,
        verbose=2,
    )

    val_metrics = model.evaluate(X_val, y_val, verbose=0)
    metric_names = model.metrics_names
    results = dict(zip(metric_names, val_metrics))
    log.info("Validation metrics: %s", results)

    keras_path = model_dir / f"{MODEL_NAME}.keras"
    model.save(keras_path)
    log.info("Keras model → %s", keras_path)

    meta = {
        "model": MODEL_NAME,
        "n_features": X.shape[1],
        "epochs_trained": len(history.history["loss"]),
        "val_auc": float(results.get("auc", 0)),
        "val_accuracy": float(results.get("accuracy", 0)),
        "occupancy_threshold": 0.6,
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
