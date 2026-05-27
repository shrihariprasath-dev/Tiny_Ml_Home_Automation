"""
ai_main.py — Standalone FastAPI AI Inference Service (port 8001).

Serves the two server-side models (forecast, appliance classification)
that are too large for the ESP32, and proxies anomaly/occupancy results
from InfluxDB for the main API.

Endpoints:
    GET  /forecast?device_id=    next-hour kWh prediction
    GET  /anomalies?limit=       recent anomaly events from InfluxDB
    POST /occupancy              batch occupancy predictions
    POST /retrain                queue a Celery retraining task
    GET  /health
    GET  /metrics                Prometheus scrape target
"""

import logging
import json
import numpy as np
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import get_settings
from app.core.database import get_influx_client, close_influx_client

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
settings = get_settings()

MODEL_DIR = Path("ml/models")

# ── TFLite runtime ────────────────────────────────────────────────────────────

try:
    import tflite_runtime.interpreter as tflite
    _TFLITE_LIB = "tflite_runtime"
except ImportError:
    import tensorflow as tf
    tflite = tf.lite
    _TFLITE_LIB = "tensorflow"

log.info("TFLite backend: %s", _TFLITE_LIB)


class TFLiteModel:
    """Thin wrapper around a TFLite Interpreter."""

    def __init__(self, path: Path) -> None:
        self.interpreter = tflite.Interpreter(model_path=str(path))
        self.interpreter.allocate_tensors()
        self.input_details  = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.input_scale    = self.input_details[0]["quantization"][0]
        self.input_zp       = self.input_details[0]["quantization"][1]
        self.output_scale   = self.output_details[0]["quantization"][0]
        self.output_zp      = self.output_details[0]["quantization"][1]
        log.info("Loaded TFLite model: %s", path.name)

    def predict(self, x: np.ndarray) -> np.ndarray:
        """Quantize input → invoke → dequantize output."""
        if self.input_scale != 0:
            x_q = (x / self.input_scale + self.input_zp).astype(np.int8)
        else:
            x_q = x.astype(np.int8)

        self.interpreter.set_tensor(self.input_details[0]["index"], x_q)
        self.interpreter.invoke()
        out_q = self.interpreter.get_tensor(self.output_details[0]["index"])

        if self.output_scale != 0:
            return (out_q.astype(np.float32) - self.output_zp) * self.output_scale
        return out_q.astype(np.float32)


# Model registry — populated at startup
_models: dict[str, TFLiteModel] = {}


def _load_models() -> None:
    for name in ("model_forecast", "model_appliance"):
        path = MODEL_DIR / f"{name}.tflite"
        if path.exists():
            _models[name] = TFLiteModel(path)
        else:
            log.warning("TFLite model not found: %s — endpoint will return 503", path)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_models()
    log.info("AI service ready — models: %s", list(_models.keys()))
    yield
    await close_influx_client()


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Smart Home AI Service",
    version="1.0.0",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app)


# ── Schemas ───────────────────────────────────────────────────────────────────

class OccupancyRequest(BaseModel):
    device_ids: list[str]


class RetrainRequest(BaseModel):
    model: str = "anomaly"


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _query_influx_last(device_id: str, field: str,
                              window: str = "-5m") -> float | None:
    client = get_influx_client()
    query_api = client.query_api()
    flux = f"""
        from(bucket: "{settings.influx_bucket}")
          |> range(start: {window})
          |> filter(fn: (r) => r._measurement == "energy_telemetry")
          |> filter(fn: (r) => r["device_id"] == "{device_id}")
          |> filter(fn: (r) => r._field == "{field}")
          |> last()
    """
    try:
        tables = await query_api.query(flux)
        for table in tables:
            for record in table.records:
                return float(record.get_value())
    except Exception as exc:
        log.error("InfluxDB query failed: %s", exc)
    return None


async def _query_influx_window(device_id: str, field: str,
                                n_hours: int = 24) -> np.ndarray:
    client = get_influx_client()
    query_api = client.query_api()
    flux = f"""
        from(bucket: "{settings.influx_bucket}")
          |> range(start: -{n_hours}h)
          |> filter(fn: (r) => r._measurement == "energy_telemetry")
          |> filter(fn: (r) => r["device_id"] == "{device_id}")
          |> filter(fn: (r) => r._field == "{field}")
          |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
    """
    values = []
    try:
        tables = await query_api.query(flux)
        for table in tables:
            for record in table.records:
                values.append(float(record.get_value()))
    except Exception as exc:
        log.error("InfluxDB window query failed: %s", exc)
    return np.array(values, dtype=np.float32)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/forecast")
async def forecast(device_id: str = Query(...)):
    if "model_forecast" not in _models:
        raise HTTPException(503, "Forecast model not loaded")

    kwh_window = await _query_influx_window(device_id, "energy_kwh", n_hours=24)

    if len(kwh_window) < 24:
        # Pad with last known value if not enough history
        pad_len  = 24 - len(kwh_window)
        last_val = float(kwh_window[-1]) if len(kwh_window) > 0 else 0.0
        kwh_window = np.concatenate([
            np.full(pad_len, last_val, dtype=np.float32), kwh_window
        ])

    x = kwh_window[-24:].reshape(1, 24, 1)
    pred_norm = float(_models["model_forecast"].predict(x)[0][0])

    # De-normalise using fixed range (update from norm_stats.csv in production)
    pred_kwh = max(0.0, pred_norm)

    return {
        "device_id":   device_id,
        "next_hour_kwh": round(pred_kwh, 4),
        "unit": "kWh",
        "confidence": "medium",
    }


@app.get("/anomalies")
async def anomalies(
    device_id: str | None = Query(None),
    limit: int             = Query(50, le=500),
):
    client = get_influx_client()
    query_api = client.query_api()

    device_filter = ""
    if device_id:
        device_filter = f'|> filter(fn: (r) => r["device_id"] == "{device_id}")'

    meta_path = MODEL_DIR / "model_anomaly_meta.json"
    threshold = 0.5
    if meta_path.exists():
        threshold = json.loads(meta_path.read_text()).get("threshold", 0.5)

    flux = f"""
        from(bucket: "{settings.influx_bucket}")
          |> range(start: -7d)
          |> filter(fn: (r) => r._measurement == "energy_telemetry")
          {device_filter}
          |> filter(fn: (r) => r._field == "anomaly_score")
          |> filter(fn: (r) => r._value > {threshold})
          |> sort(columns: ["_time"], desc: true)
          |> limit(n: {limit})
    """
    results = []
    try:
        tables = await query_api.query(flux)
        for table in tables:
            for record in table.records:
                results.append({
                    "time":         record.get_time().isoformat(),
                    "device_id":    record.values.get("device_id", ""),
                    "anomaly_score":round(float(record.get_value()), 4),
                })
    except Exception as exc:
        log.error("Anomaly query error: %s", exc)

    return results


@app.post("/occupancy")
async def occupancy(req: OccupancyRequest):
    results = []
    for device_id in req.device_ids:
        occ_prob = await _query_influx_last(device_id, "occupancy_prob")
        results.append({
            "device_id":      device_id,
            "occupancy_prob": round(occ_prob, 4) if occ_prob is not None else None,
            "occupied":       (occ_prob or 0) >= 0.6,
        })
    return results


@app.post("/retrain")
async def retrain(req: RetrainRequest):
    from app.services.alert_engine import trigger_model_retrain
    task = trigger_model_retrain.delay(req.model)
    return {
        "task_id": task.id,
        "status":  "queued",
        "model":   req.model,
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "models_loaded": list(_models.keys()),
    }
