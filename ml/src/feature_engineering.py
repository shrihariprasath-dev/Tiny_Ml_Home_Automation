"""
feature_engineering.py — Stage 2 of the TinyML training pipeline.

Reads the clean dataset and produces:
  - Rolling statistics (mean, std) over 5 / 10 / 30 sample windows
  - Time-of-day and day-of-week features (sine/cosine encoded)
  - Lag features for power_w
  - Rate-of-change features
  - Sliding-window sequences for LSTM models
  - Occupancy labels (heuristic, refined with PIR + power)

Outputs:
  ml/data/features/features.csv       — flat feature frame
  ml/data/features/sequences_X.npy   — (N, 10, F) LSTM input windows
  ml/data/features/sequences_y.npy   — (N,) reconstruction targets (anomaly)
  ml/data/features/forecast_X.npy    — (N, 24, 1) hourly kWh sequences
  ml/data/features/forecast_y.npy    — (N,) next-hour kWh targets
  ml/data/features/occupancy_X.npy   — (N, F) flat occupancy features
  ml/data/features/occupancy_y.npy   — (N,) binary occupancy labels
  ml/data/features/appliance_X.npy   — (N, 50, 1) power waveform windows
  ml/data/features/appliance_y.npy   — (N,) class labels
"""

import argparse
import logging
import numpy as np
import pandas as pd
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

WINDOW_SIZES   = [5, 10, 30]
LAG_STEPS      = [1, 5, 10]
SEQ_LEN        = 10    # anomaly LSTM window
FORECAST_WIN   = 24    # hourly samples for energy forecast
APPLIANCE_WIN  = 50    # power waveform samples for CNN


# ── Time encoding ─────────────────────────────────────────────────────────────

def encode_time(df: pd.DataFrame) -> pd.DataFrame:
    ts = df["timestamp"]
    hour   = ts.dt.hour + ts.dt.minute / 60.0
    dow    = ts.dt.dayofweek.astype(float)

    # Sine/cosine cyclical encoding — avoids discontinuity at 23→0 and Sun→Mon
    df["hour_sin"]  = np.sin(2 * np.pi * hour / 24.0)
    df["hour_cos"]  = np.cos(2 * np.pi * hour / 24.0)
    df["dow_sin"]   = np.sin(2 * np.pi * dow  / 7.0)
    df["dow_cos"]   = np.cos(2 * np.pi * dow  / 7.0)
    df["is_weekend"]= (dow >= 5).astype(float)
    return df


# ── Rolling statistics ────────────────────────────────────────────────────────

def add_rolling(df: pd.DataFrame) -> pd.DataFrame:
    for w in WINDOW_SIZES:
        df[f"power_roll_mean_{w}"] = df["power_w"].rolling(w, min_periods=1).mean()
        df[f"power_roll_std_{w}"]  = df["power_w"].rolling(w, min_periods=1).std().fillna(0)
    return df


# ── Lag features ──────────────────────────────────────────────────────────────

def add_lags(df: pd.DataFrame) -> pd.DataFrame:
    for lag in LAG_STEPS:
        df[f"power_lag_{lag}"] = df["power_w"].shift(lag).fillna(method="bfill")
    df["power_roc"] = df["power_w"].diff().fillna(0)   # rate of change
    return df


# ── Occupancy labelling (heuristic) ──────────────────────────────────────────

def label_occupancy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Label a sample as occupied when:
      - PIR motion detected, OR
      - power_w > 50 W (idle threshold) AND hour between 06:00–23:00
    Refined to 0/1 binary.
    """
    hour = df["timestamp"].dt.hour
    occupied = (
        df["motion"].astype(bool) |
        ((df["power_w"] > 50) & (hour >= 6) & (hour < 23))
    )
    df["occupancy"] = occupied.astype(int)
    log.info("Occupancy: %d occupied / %d total (%.1f%%)",
             occupied.sum(), len(df), 100 * occupied.mean())
    return df


# ── Sequence builders ─────────────────────────────────────────────────────────

def build_lstm_sequences(series: np.ndarray, seq_len: int):
    """Build sliding windows of shape (N, seq_len, 1)."""
    X, y = [], []
    for i in range(len(series) - seq_len):
        X.append(series[i : i + seq_len])
        y.append(series[i + seq_len])
    return np.array(X)[..., np.newaxis], np.array(y)


def build_appliance_sequences(power: np.ndarray, labels: np.ndarray, win: int):
    """Build fixed-length power waveform windows with appliance class labels."""
    X, y = [], []
    for i in range(len(power) - win):
        X.append(power[i : i + win])
        y.append(labels[i + win])
    return np.array(X)[..., np.newaxis], np.array(y)


def build_forecast_sequences(hourly_kwh: np.ndarray, win: int):
    X, y = [], []
    for i in range(len(hourly_kwh) - win):
        X.append(hourly_kwh[i : i + win])
        y.append(hourly_kwh[i + win])
    return np.array(X)[..., np.newaxis], np.array(y)


# ── Appliance label synthesis ─────────────────────────────────────────────────

def synthesise_appliance_labels(power_w: np.ndarray) -> np.ndarray:
    """
    Heuristic class labels from power level bands.
    Replace with ground-truth labels from a plug-level dataset when available.
    Classes: 0=idle, 1=lighting, 2=fan, 3=AC, 4=other
    """
    labels = np.zeros(len(power_w), dtype=np.int32)
    labels[power_w > 10]   = 1   # lighting
    labels[power_w > 80]   = 2   # fan
    labels[power_w > 600]  = 3   # AC
    labels[power_w > 2000] = 4   # other high-load
    return labels


# ── Main ──────────────────────────────────────────────────────────────────────

def engineer(clean_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(clean_path, parse_dates=["timestamp"])
    log.info("Loaded %d rows", len(df))

    df = encode_time(df)
    df = add_rolling(df)
    df = add_lags(df)
    df = label_occupancy(df)

    df.to_csv(out_dir / "features.csv", index=False)
    log.info("Feature frame → %s/features.csv", out_dir)

    # Anomaly LSTM sequences (power_w_norm)
    power_norm = df["power_w_norm"].values
    X_seq, y_seq = build_lstm_sequences(power_norm, SEQ_LEN)
    np.save(out_dir / "sequences_X.npy", X_seq)
    np.save(out_dir / "sequences_y.npy", y_seq)
    log.info("Anomaly sequences: X=%s  y=%s", X_seq.shape, y_seq.shape)

    # Occupancy flat features
    occ_cols = [
        "power_w_norm", "motion", "temperature_norm", "humidity_norm",
        "hour_sin", "hour_cos", "dow_sin", "dow_cos", "is_weekend",
    ]
    X_occ = df[occ_cols].values.astype(np.float32)
    y_occ = df["occupancy"].values.astype(np.float32)
    np.save(out_dir / "occupancy_X.npy", X_occ)
    np.save(out_dir / "occupancy_y.npy", y_occ)
    log.info("Occupancy features: X=%s  y=%s", X_occ.shape, y_occ.shape)

    # Hourly kWh forecast sequences
    hourly = df.set_index("timestamp")["energy_kwh_norm"].resample("1h").mean().dropna().values
    if len(hourly) > FORECAST_WIN + 1:
        X_fc, y_fc = build_forecast_sequences(hourly, FORECAST_WIN)
        np.save(out_dir / "forecast_X.npy", X_fc)
        np.save(out_dir / "forecast_y.npy", y_fc)
        log.info("Forecast sequences: X=%s  y=%s", X_fc.shape, y_fc.shape)
    else:
        log.warning("Not enough hourly data for forecast sequences (need >%d hours)", FORECAST_WIN)

    # Appliance CNN sequences
    app_labels = synthesise_appliance_labels(df["power_w"].values)
    X_app, y_app = build_appliance_sequences(power_norm, app_labels, APPLIANCE_WIN)
    np.save(out_dir / "appliance_X.npy", X_app)
    np.save(out_dir / "appliance_y.npy", y_app)
    log.info("Appliance sequences: X=%s  y=%s  classes=%d",
             X_app.shape, y_app.shape, len(np.unique(y_app)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean",  default="ml/data/processed/clean.csv")
    ap.add_argument("--outdir", default="ml/data/features")
    args = ap.parse_args()
    engineer(Path(args.clean), Path(args.outdir))
