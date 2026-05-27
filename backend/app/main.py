import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from app.core.config import get_settings
from app.core.database import create_tables, close_influx_client
from app.routers import auth, devices, energy, alerts, ai

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
settings = get_settings()

# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting Smart Home API v%s", settings.app_version)
    await create_tables()

    # Start MQTT bridge as background task
    from app.services.mqtt_bridge import run_mqtt_bridge
    mqtt_task = asyncio.create_task(run_mqtt_bridge())
    log.info("MQTT bridge task started")

    yield

    mqtt_task.cancel()
    try:
        await mqtt_task
    except asyncio.CancelledError:
        pass
    await close_influx_client()
    log.info("Smart Home API shutdown complete")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — tighten origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics at /metrics
Instrumentator().instrument(app).expose(app)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(energy.router)
app.include_router(alerts.router)
app.include_router(ai.router)


# ── OTA endpoint ─────────────────────────────────────────────────────────────

@app.get("/ota/version")
async def ota_version():
    """Polled by ESP32 ota_task every hour to check for firmware updates."""
    import os, glob
    pattern = os.path.join(settings.ota_firmware_path, "*.bin")
    bins = sorted(glob.glob(pattern))
    if not bins:
        return {"version": "0.0.0", "url": ""}
    latest = bins[-1]
    version = os.path.basename(latest).replace("firmware_", "").replace(".bin", "")
    return {
        "version": version,
        "url": f"/ota/firmware/{os.path.basename(latest)}",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.app_version}


# ── Global error handler ──────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
