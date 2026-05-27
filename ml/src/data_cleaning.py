"""
data_cleaning.py — Stage 1 of the TinyML training pipeline.

Reads raw sensor CSV, removes outliers, fills gaps,
normalises features, and writes a clean dataset ready
for feature engineering.

Expected CSV columns:
    timestamp, voltage, current, power_w, power_factor,
    energy_kwh, temperature, humidity, motion
"""

import argparse
import logging
import numpy as np
import pandas as pd
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── Column definitions ────────────────────────────────────────────────────────

NUMERIC_COLS = [
    "voltage", "current", "power_w", "power_factor",
    "energy_kwh", "temperature", "humidity",
]
BOOL_COLS   = ["motion"]
ALL_COLS    = ["timestamp"] + NUMERIC_COLS + BOOL_COLS

# Physically valid ranges — readings outside are sensor errors
VALID_RANGES = {
    "voltage":      (180.0,  260.0),
    "current":      (0.0,    20.0),
    "power_w":      (0.0,    5000.0),
    "power_factor": (0.0,    1.0),
    "energy_kwh":   (0.0,    1e6),
    "temperature":  (-10.0,  60.0),
    "humidity":     (0.0,    100.0),
}

# Normalisation stats saved alongside the clean CSV
# (loaded by feature_engineering.py and convert_tflite.py)
NORM_STATS_FILE = "norm_stats.csv"


def load_raw(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    log.info("Loaded %d rows from %s", len(df), path)

    # Coerce numeric columns — non-parsable become NaN
    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["motion"] = df["motion"].astype(bool)
    return df


def remove_range_outliers(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    for col, (lo, hi) in VALID_RANGES.items():
        mask = df[col].between(lo, hi) | df[col].isna()
        df.loc[~mask, col] = np.nan
    log.info("Range filter: %d NaNs introduced", df[NUMERIC_COLS].isna().sum().sum())
    return df


def remove_iqr_outliers(df: pd.DataFrame, k: float = 3.0) -> pd.DataFrame:
    """Replace values beyond k × IQR from Q1/Q3 with NaN."""
    for col in NUMERIC_COLS:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lo, hi = q1 - k * iqr, q3 + k * iqr
        outliers = ~df[col].between(lo, hi) & df[col].notna()
        df.loc[outliers, col] = np.nan
        if outliers.sum():
            log.info("IQR (%s): %d outliers → NaN", col, outliers.sum())
    return df


def fill_gaps(df: pd.DataFrame, max_gap_fill: int = 10) -> pd.DataFrame:
    """
    Forward-fill short gaps (≤ max_gap_fill consecutive NaNs).
    Remaining NaN rows are dropped.
    """
    df[NUMERIC_COLS] = (
        df[NUMERIC_COLS]
        .fillna(method="ffill", limit=max_gap_fill)
        .fillna(method="bfill", limit=max_gap_fill)
    )
    before = len(df)
    df = df.dropna(subset=NUMERIC_COLS).reset_index(drop=True)
    log.info("Gap fill: dropped %d rows with unfillable NaN", before - len(df))
    return df


def compute_norm_stats(df: pd.DataFrame) -> pd.DataFrame:
    stats = pd.DataFrame({
        "col":  NUMERIC_COLS,
        "mean": [df[c].mean() for c in NUMERIC_COLS],
        "std":  [df[c].std()  for c in NUMERIC_COLS],
        "min":  [df[c].min()  for c in NUMERIC_COLS],
        "max":  [df[c].max()  for c in NUMERIC_COLS],
    })
    return stats


def min_max_normalise(df: pd.DataFrame, stats: pd.DataFrame) -> pd.DataFrame:
    for _, row in stats.iterrows():
        col = row["col"]
        rng = row["max"] - row["min"]
        if rng < 1e-9:
            rng = 1.0
        df[f"{col}_norm"] = (df[col] - row["min"]) / rng
    return df


def clean(raw_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_raw(raw_path)
    df = remove_range_outliers(df)
    df = remove_iqr_outliers(df)
    df = fill_gaps(df)

    stats = compute_norm_stats(df)
    df    = min_max_normalise(df, stats)

    clean_path = out_dir / "clean.csv"
    stats_path = out_dir / NORM_STATS_FILE

    df.to_csv(clean_path, index=False)
    stats.to_csv(stats_path, index=False)

    log.info("Clean dataset: %d rows → %s", len(df), clean_path)
    log.info("Norm stats    → %s", stats_path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input",  default="ml/data/raw/telemetry.csv")
    ap.add_argument("--outdir", default="ml/data/processed")
    args = ap.parse_args()
    clean(Path(args.input), Path(args.outdir))
