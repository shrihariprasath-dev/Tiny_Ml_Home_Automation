"""
train_anomaly.py — LSTM-Autoencoder for power anomaly detection.

Architecture:
    Input   : (10, 1)  — 10-step normalised power_w sequence
    Encoder : LSTM(32, return_sequences=False)
    Bridge  : RepeatVector(10)
    Decoder : LSTM(32, return_sequences=True)
    Output  : TimeDistributed(Dense(1))

Loss:  MSE (reconstruction error)
Metric used at inference: mean reconstruction error over the window.
Anomaly threshold = mean_train_error + 2 × std_train_error
"""

import argparse
import logging
import numpy as np
import json
from pathlib import Path
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

MODEL_NAME  = "model_anomaly"
SEQ_LEN     = 10
N_FEATURES  = 1


def build_model(seq_len: int = SEQ_LEN) -> keras.Model:
    inp = keras.Input(shape=(seq_len, N_FEATURES), name="power_sequence")

    # Encoder
    encoded = layers.LSTM(32, activation="tanh", name="encoder")(inp)

    # Bridge
    repeated = layers.RepeatVector(seq_len, name="bridge")(encoded)

    # Decoder
    decoded = layers.LSTM(32, activation="tanh",
                          return_sequences=True, name="decoder")(repeated)
    out = layers.TimeDistributed(layers.Dense(N_FEATURES), name="reconstruction")(decoded)

    model = keras.Model(inputs=inp, outputs=out, name="lstm_autoencoder")
    model.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
    return model


def compute_threshold(model: keras.Model,
                       X_train: np.ndarray) -> tuple[float, float]:
    X_pred   = model.predict(X_train, verbose=0)
    errors   = np.mean(np.square(X_train - X_pred), axis=(1, 2))
    mean_err = float(np.mean(errors))
    std_err  = float(np.std(errors))
    threshold = mean_err + 2 * std_err
    log.info("Train reconstruction error: mean=%.5f  std=%.5f  threshold=%.5f",
             mean_err, std_err, threshold)
    return threshold, mean_err


def train(feat_dir: Path, model_dir: Path) -> None:
    model_dir.mkdir(parents=True, exist_ok=True)

    X = np.load(feat_dir / "sequences_X.npy").astype(np.float32)
    log.info("Loaded sequences X=%s", X.shape)

    # Autoencoder: input == target
    X_train, X_val = train_test_split(X, test_size=0.15, random_state=42)

    model = build_model()
    model.summary(print_fn=log.info)

    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=10,
            restore_best_weights=True, verbose=1
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=5, verbose=1
        ),
        keras.callbacks.ModelCheckpoint(
            filepath=str(model_dir / f"{MODEL_NAME}_best.keras"),
            monitor="val_loss", save_best_only=True
        ),
    ]

    history = model.fit(
        X_train, X_train,
        validation_data=(X_val, X_val),
        epochs=100,
        batch_size=64,
        callbacks=callbacks,
        verbose=2,
    )

    threshold, mean_err = compute_threshold(model, X_train)

    # Save Keras model
    keras_path = model_dir / f"{MODEL_NAME}.keras"
    model.save(keras_path)
    log.info("Keras model → %s", keras_path)

    # Save threshold metadata
    meta = {
        "model": MODEL_NAME,
        "threshold": threshold,
        "mean_train_error": mean_err,
        "seq_len": SEQ_LEN,
        "n_features": N_FEATURES,
        "epochs_trained": len(history.history["loss"]),
        "final_val_loss": float(min(history.history["val_loss"])),
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
