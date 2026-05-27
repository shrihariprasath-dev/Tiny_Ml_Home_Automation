"""
convert_tflite.py — TFLite INT8 post-training quantization.

Implements the exact conversion settings from the README architecture spec:

    converter.optimizations        = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.ops      = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type= tf.int8
    representative_dataset         = representative_data_gen()

Each model is converted separately. A representative dataset
of 200 samples is drawn from the feature files so the quantizer
can calibrate scale/zero_point for every tensor.

Outputs (to ml/models/):
    model_anomaly.tflite
    model_occupancy.tflite
    model_forecast.tflite
    model_appliance.tflite
"""

import argparse
import logging
import numpy as np
import tensorflow as tf
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

N_REPRESENTATIVE = 200


def make_representative_gen(data: np.ndarray):
    """Yields batches of 1 sample — required by TFLiteConverter."""
    indices = np.random.choice(len(data), size=N_REPRESENTATIVE, replace=False)
    def gen():
        for i in indices:
            yield [data[i : i + 1].astype(np.float32)]
    return gen


def convert_model(keras_path: Path, tflite_path: Path,
                   rep_data: np.ndarray) -> int:
    log.info("Converting %s → %s", keras_path.name, tflite_path.name)

    model = tf.keras.models.load_model(keras_path)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)

    # ── INT8 quantization — exact settings from README ────────────────────
    converter.optimizations         = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type  = tf.int8
    converter.inference_output_type = tf.int8
    converter.representative_dataset = make_representative_gen(rep_data)
    # ─────────────────────────────────────────────────────────────────────

    tflite_model = converter.convert()
    tflite_path.write_bytes(tflite_model)
    size_kb = len(tflite_model) / 1024
    log.info("  ✓ %s  (%.1f KB)", tflite_path.name, size_kb)
    return len(tflite_model)


def convert_all(model_dir: Path, feat_dir: Path) -> None:
    model_dir.mkdir(parents=True, exist_ok=True)

    jobs = {
        "model_anomaly": {
            "feat_file": feat_dir / "sequences_X.npy",
        },
        "model_occupancy": {
            "feat_file": feat_dir / "occupancy_X.npy",
        },
        "model_forecast": {
            "feat_file": feat_dir / "forecast_X.npy",
        },
        "model_appliance": {
            "feat_file": feat_dir / "appliance_X.npy",
        },
    }

    total_bytes = 0
    for name, cfg in jobs.items():
        keras_path  = model_dir / f"{name}.keras"
        tflite_path = model_dir / f"{name}.tflite"
        feat_file   = cfg["feat_file"]

        if not keras_path.exists():
            log.warning("Keras model not found: %s — skipping", keras_path)
            continue
        if not feat_file.exists():
            log.warning("Feature file not found: %s — skipping", feat_file)
            continue

        rep_data = np.load(feat_file)
        total_bytes += convert_model(keras_path, tflite_path, rep_data)

    log.info("Total TFLite output: %.1f KB", total_bytes / 1024)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_dir", default="ml/models")
    ap.add_argument("--feat_dir",  default="ml/data/features")
    ap.add_argument("--seed",      type=int, default=42)
    args = ap.parse_args()
    np.random.seed(args.seed)
    convert_all(Path(args.model_dir), Path(args.feat_dir))
