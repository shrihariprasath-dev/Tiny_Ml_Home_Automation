"""
model_evaluate.py — Unified evaluation for all four TinyML models.

Outputs:
  - Classification report (occupancy, appliance)
  - Confusion matrix (saved as PNG)
  - ROC-AUC (occupancy)
  - MAE / RMSE (forecast)
  - Reconstruction error distribution + threshold (anomaly)
  - JSON summary written to ml/models/{model}_eval.json
"""

import argparse
import json
import logging
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    mean_absolute_error, mean_squared_error,
)
import tensorflow as tf

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


def eval_anomaly(model_dir: Path, feat_dir: Path) -> dict:
    log.info("─── Evaluating anomaly model ───")
    model = tf.keras.models.load_model(model_dir / "model_anomaly.keras")
    X = np.load(feat_dir / "sequences_X.npy").astype(np.float32)

    X_pred  = model.predict(X, verbose=0)
    errors  = np.mean(np.square(X - X_pred), axis=(1, 2))

    meta_path = model_dir / "model_anomaly_meta.json"
    threshold = json.loads(meta_path.read_text())["threshold"] if meta_path.exists() else 0.5

    n_anomalies = int((errors > threshold).sum())
    log.info("Reconstruction error — mean=%.5f  std=%.5f  threshold=%.5f",
             errors.mean(), errors.std(), threshold)
    log.info("Samples above threshold: %d / %d (%.1f%%)",
             n_anomalies, len(errors), 100 * n_anomalies / len(errors))

    # Plot error distribution
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(errors, bins=80, color="steelblue", alpha=0.8)
    ax.axvline(threshold, color="red", linestyle="--", label=f"Threshold={threshold:.4f}")
    ax.set_xlabel("Reconstruction Error (MSE)")
    ax.set_ylabel("Count")
    ax.set_title("Anomaly Model — Reconstruction Error Distribution")
    ax.legend()
    fig.tight_layout()
    fig.savefig(model_dir / "model_anomaly_error_dist.png", dpi=120)
    plt.close(fig)

    result = {
        "model": "anomaly",
        "mean_error": float(errors.mean()),
        "std_error": float(errors.std()),
        "threshold": threshold,
        "anomaly_rate_pct": round(100 * n_anomalies / len(errors), 2),
    }
    (model_dir / "model_anomaly_eval.json").write_text(json.dumps(result, indent=2))
    return result


def eval_occupancy(model_dir: Path, feat_dir: Path) -> dict:
    log.info("─── Evaluating occupancy model ───")
    model  = tf.keras.models.load_model(model_dir / "model_occupancy.keras")
    X = np.load(feat_dir / "occupancy_X.npy").astype(np.float32)
    y = np.load(feat_dir / "occupancy_y.npy").astype(np.float32)

    probs  = model.predict(X, verbose=0).flatten()
    preds  = (probs >= 0.6).astype(int)
    auc    = roc_auc_score(y.astype(int), probs)
    report = classification_report(y.astype(int), preds,
                                   target_names=["not_occupied", "occupied"],
                                   output_dict=True)
    log.info("ROC-AUC: %.4f", auc)
    log.info("\n%s", classification_report(y.astype(int), preds,
             target_names=["not_occupied", "occupied"]))

    cm = confusion_matrix(y.astype(int), preds)
    _save_confusion_matrix(cm, ["not_occupied", "occupied"],
                            model_dir / "model_occupancy_cm.png",
                            title="Occupancy Model")

    result = {"model": "occupancy", "roc_auc": float(auc),
              "report": report}
    (model_dir / "model_occupancy_eval.json").write_text(json.dumps(result, indent=2))
    return result


def eval_forecast(model_dir: Path, feat_dir: Path) -> dict:
    log.info("─── Evaluating forecast model ───")
    fc_x = feat_dir / "forecast_X.npy"
    fc_y = feat_dir / "forecast_y.npy"
    if not fc_x.exists():
        log.warning("forecast_X.npy missing — skipping forecast evaluation")
        return {}

    model = tf.keras.models.load_model(model_dir / "model_forecast.keras")
    X = np.load(fc_x).astype(np.float32)
    y = np.load(fc_y).astype(np.float32)

    y_pred = model.predict(X, verbose=0).flatten()
    mae    = float(mean_absolute_error(y, y_pred))
    rmse   = float(np.sqrt(mean_squared_error(y, y_pred)))
    log.info("Forecast MAE=%.5f  RMSE=%.5f", mae, rmse)

    # Plot predicted vs actual (first 200 samples)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(y[:200],      label="Actual",    alpha=0.8)
    ax.plot(y_pred[:200], label="Predicted", alpha=0.8)
    ax.set_title("Energy Forecast — Predicted vs Actual (first 200 samples)")
    ax.set_xlabel("Sample")
    ax.set_ylabel("kWh (normalised)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(model_dir / "model_forecast_pred_vs_actual.png", dpi=120)
    plt.close(fig)

    result = {"model": "forecast", "mae": mae, "rmse": rmse}
    (model_dir / "model_forecast_eval.json").write_text(json.dumps(result, indent=2))
    return result


def eval_appliance(model_dir: Path, feat_dir: Path) -> dict:
    log.info("─── Evaluating appliance model ───")
    model  = tf.keras.models.load_model(model_dir / "model_appliance.keras")
    X = np.load(feat_dir / "appliance_X.npy").astype(np.float32)
    y = np.load(feat_dir / "appliance_y.npy").astype(np.int32)

    probs  = model.predict(X, verbose=0)
    preds  = np.argmax(probs, axis=1)
    names  = ["idle", "lighting", "fan", "AC", "other"][:probs.shape[1]]
    report = classification_report(y, preds, target_names=names, output_dict=True)
    log.info("\n%s", classification_report(y, preds, target_names=names))

    cm = confusion_matrix(y, preds)
    _save_confusion_matrix(cm, names, model_dir / "model_appliance_cm.png",
                            title="Appliance Classification Model")

    result = {"model": "appliance", "report": report}
    (model_dir / "model_appliance_eval.json").write_text(json.dumps(result, indent=2))
    return result


def _save_confusion_matrix(cm: np.ndarray, labels: list,
                             path: Path, title: str) -> None:
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    fig.colorbar(im)
    ax.set(xticks=range(len(labels)), yticks=range(len(labels)),
           xticklabels=labels, yticklabels=labels,
           title=title, ylabel="True", xlabel="Predicted")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    thresh = cm.max() / 2
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, cm[i, j], ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    log.info("Confusion matrix → %s", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_dir", default="ml/models")
    ap.add_argument("--feat_dir",  default="ml/data/features")
    ap.add_argument("--models", nargs="+",
                    default=["anomaly", "occupancy", "forecast", "appliance"])
    args = ap.parse_args()

    md = Path(args.model_dir)
    fd = Path(args.feat_dir)
    dispatch = {
        "anomaly":    eval_anomaly,
        "occupancy":  eval_occupancy,
        "forecast":   eval_forecast,
        "appliance":  eval_appliance,
    }
    for m in args.models:
        if m in dispatch:
            dispatch[m](md, fd)
