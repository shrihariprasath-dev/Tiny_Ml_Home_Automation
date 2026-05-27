from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.device import Device
from app.models.user import User
from app.schemas.energy import EnergyPoint, EnergySummary, RoomEnergy
from app.services import influx_client as influx
from datetime import datetime, timezone

router = APIRouter(prefix="/api/energy", tags=["energy"])


@router.get("/realtime")
async def get_realtime(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Device.device_id).where(Device.owner_id == current_user.id)
    )
    device_ids = [row[0] for row in result.all()]
    return await influx.query_realtime(device_ids)


@router.get("/history", response_model=list[EnergyPoint])
async def get_history(
    device_id: str = Query(...),
    from_ts: datetime = Query(..., alias="from"),
    to_ts: datetime   = Query(..., alias="to"),
    current_user: User = Depends(get_current_user),
):
    return await influx.query_history(device_id, from_ts, to_ts)


@router.get("/summary", response_model=EnergySummary)
async def get_summary(
    device_id: str = Query(...),
    period: str    = Query("daily", pattern="^(daily|monthly)$"),
    current_user: User = Depends(get_current_user),
):
    return await influx.query_summary(device_id, period)


@router.get("/rooms", response_model=list[RoomEnergy])
async def get_rooms(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Device.room).where(
            Device.owner_id == current_user.id,
            Device.room.isnot(None),
        ).distinct()
    )
    rooms = [row[0] for row in result.all()]
    return await influx.query_room_breakdown(rooms)
