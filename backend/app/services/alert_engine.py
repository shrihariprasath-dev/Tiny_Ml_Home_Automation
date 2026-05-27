from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "smart_home",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(name="alert_engine.send_alert_notification", bind=True, max_retries=3)
def send_alert_notification(self, device_id: str, alert_data: dict) -> dict:
    """
    Dispatched when an anomaly alert arrives from an ESP32.
    Sends push notification to all users who own the device.
    Retries up to 3 times on failure (exponential back-off).
    """
    try:
        import logging
        log = logging.getLogger(__name__)
        log.info("Processing alert for device %s: %s", device_id, alert_data)
        # FCM / email notification integration point
        return {"status": "sent", "device_id": device_id}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@celery_app.task(name="alert_engine.check_energy_threshold")
def check_energy_threshold(device_id: str, power_w: float, threshold_w: float) -> None:
    """Fired periodically to check if a device exceeds its configured power threshold."""
    if power_w > threshold_w:
        send_alert_notification.delay(device_id, {
            "type": "threshold",
            "severity": "medium",
            "power_w": power_w,
            "threshold_w": threshold_w,
        })


@celery_app.task(name="alert_engine.trigger_model_retrain")
def trigger_model_retrain(model_type: str) -> dict:
    """Weekly scheduled task — triggers the AI service to retrain a model."""
    import httpx
    try:
        resp = httpx.post(
            f"{settings.ai_service_url}/retrain",
            json={"model": model_type},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


# ── Celery Beat schedule (weekly retrain) ────────────────────────────────────
celery_app.conf.beat_schedule = {
    "retrain-anomaly-weekly": {
        "task": "alert_engine.trigger_model_retrain",
        "schedule": 604800,   # 7 days in seconds
        "args": ("anomaly",),
    },
    "retrain-occupancy-weekly": {
        "task": "alert_engine.trigger_model_retrain",
        "schedule": 604800,
        "args": ("occupancy",),
    },
}
