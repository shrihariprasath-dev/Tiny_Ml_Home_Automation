import httpx
import logging
from app.core.config import get_settings

log = logging.getLogger(__name__)
settings = get_settings()


async def get_forecast(device_id: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.ai_service_url}/forecast",
            params={"device_id": device_id},
        )
        resp.raise_for_status()
        return resp.json()


async def get_anomalies(device_id: str | None, limit: int) -> list[dict]:
    params = {"limit": limit}
    if device_id:
        params["device_id"] = device_id
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.ai_service_url}/anomalies", params=params
        )
        resp.raise_for_status()
        return resp.json()


async def get_occupancy(device_ids: list[str]) -> list[dict]:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{settings.ai_service_url}/occupancy",
            json={"device_ids": device_ids},
        )
        resp.raise_for_status()
        return resp.json()


async def trigger_retrain(model_type: str) -> dict:
    from app.services.alert_engine import trigger_model_retrain
    task = trigger_model_retrain.delay(model_type)
    return {"task_id": task.id, "status": "queued", "model": model_type}
