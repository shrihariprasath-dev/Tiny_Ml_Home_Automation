"""
train_forecast.py — Stacked LSTM for next-hour energy forecasting.

Architecture:
    Input  : (24, 1) — 24 hourly normalised kWh readings
    LSTM   : LSTM(64, return_sequences=True)
    LSTM   : LSTM(32, return_sequences=False)
    Output : Dense(1) — next-hour kWh prediction

Loss:   MAE  (mean absolute error — interpretable in kWh)
Metric: MAE, RMSE
Target INT8 size: ~55 KB
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

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

MODEL_NAME   = "model_forecast"
FORECAST_WIN = 24


def build_model(seq_len: int = FORECAST_WIN) -> keras.Model:
    inp = keras.Input(shape=(seq_len, 1), name="hourly_kwh")

    x = layers.LSTM(64, return_sequences=True, name="lstm_1")(inp)
    x = layers.Dropout(0.2)(x)
    x = layers.LSTM(32, return_sequences=False, name="lstm_2")(x)
    x = layers.Dropout(0.2)(x)

    out = layers.Dense(1, name="next_hour_kwh")(x)

    model = keras.Model(inputs=inp, outputs=out, name="energy_forecast_lstm")
    model.compile(
        optimizer=keras.optimizers.Adam(1e-3),
        loss="mae",
        metrics=[
            keras.metrics.MeanAbsoluteError(name="mae"),
            keras.metrics.RootMeanSquaredError(name="rmse"),
        ],
    )
    return model


def train(feat_dir: Path, model_dir: Path) -> None:
    model_dir.mkdir(parents=True, exist_ok=True)

    fc_x = feat_dir / "forecast_X.npy"
    fc_y = feat_dir / "forecast_y.npy"
    if not fc_x.exists():
        log.error("forecast_X.npy not found — run feature_engineering.py first")
        return

    X = np.load(fc_x).astype(np.float32)
    y = np.load(fc_y).astype(np.float32)
    log.info("Loaded forecast X=%s  y=%s", X.shape, y.shape)

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.15, random_state=42
    )

    model = build_model(seq_len=X.shape[1])
    model.summary(print_fn=log.info)

    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_mae", patience=10,
            restore_best_weights=True, verbose=1
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=5, verbose=1
        ),
        keras.callbacks.ModelCheckpoint(
            filepath=str(model_dir / f"{MODEL_NAME}_best.keras"),
            monitor="val_mae", save_best_only=True
        ),
    ]

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=150,
        batch_size=32,
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
        "seq_len": FORECAST_WIN,
        "epochs_trained": len(history.history["loss"]),
        "val_mae": float(results.get("mae", 0)),
        "val_rmse": float(results.get("rmse", 0)),
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
