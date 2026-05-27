from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.device import Device
from app.models.user import User
from app.services import ai_service

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/forecast")
async def forecast(
    device_id: str = Query(...),
    current_user: User = Depends(get_current_user),
):
    return await ai_service.get_forecast(device_id)


@router.get("/anomalies")
async def anomalies(
    device_id: str | None = Query(None),
    limit: int             = Query(50, le=500),
    current_user: User     = Depends(get_current_user),
):
    return await ai_service.get_anomalies(device_id, limit)


@router.get("/occupancy")
async def occupancy(
    current_user: User = Depends(get_current_user),
    db: AsyncSession   = Depends(get_db),
):
    result = await db.execute(
        select(Device.device_id).where(Device.owner_id == current_user.id)
    )
    device_ids = [row[0] for row in result.all()]
    return await ai_service.get_occupancy(device_ids)


@router.post("/retrain")
async def retrain(
    model: str         = Query("anomaly", pattern="^(anomaly|occupancy|forecast|appliance)$"),
    _admin: User       = Depends(require_admin),
):
    return await ai_service.trigger_retrain(model)
