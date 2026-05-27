from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.alert import Alert
from app.models.schedule import Schedule
from app.models.device import Device
from app.models.user import User
from app.schemas.alert import AlertRead, ScheduleCreate, ScheduleRead

router = APIRouter(tags=["alerts"])


# ── Alerts ────────────────────────────────────────────────────────────────────

@router.get("/api/alerts", response_model=list[AlertRead])
async def list_alerts(
    acknowledged: bool | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Alert)
        .join(Device, Alert.device_id == Device.id)
        .where(Device.owner_id == current_user.id)
        .order_by(Alert.created_at.desc())
    )
    if acknowledged is False:
        stmt = stmt.where(Alert.acknowledged_at.is_(None))
    elif acknowledged is True:
        stmt = stmt.where(Alert.acknowledged_at.isnot(None))

    result = await db.execute(stmt)
    return result.scalars().all()


@router.put("/api/alerts/{alert_id}/acknowledge", response_model=AlertRead)
async def acknowledge_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Alert)
        .join(Device, Alert.device_id == Device.id)
        .where(Alert.id == alert_id, Device.owner_id == current_user.id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged_at = datetime.now(timezone.utc)
    return alert


# ── Schedules ────────────────────────────────────────────────────────────────

@router.get("/api/schedules", response_model=list[ScheduleRead])
async def list_schedules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Schedule)
        .join(Device, Schedule.device_id == Device.id)
        .where(Device.owner_id == current_user.id)
    )
    return result.scalars().all()


@router.post("/api/schedules", response_model=ScheduleRead, status_code=201)
async def create_schedule(
    body: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    schedule = Schedule(**body.model_dump())
    db.add(schedule)
    await db.flush()
    return schedule


@router.put("/api/schedules/{schedule_id}", response_model=ScheduleRead)
async def update_schedule(
    schedule_id: int,
    body: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Schedule)
        .join(Device, Schedule.device_id == Device.id)
        .where(Schedule.id == schedule_id, Device.owner_id == current_user.id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Schedule not found")
    for k, v in body.model_dump().items():
        setattr(schedule, k, v)
    return schedule


@router.delete("/api/schedules/{schedule_id}", status_code=204)
async def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Schedule)
        .join(Device, Schedule.device_id == Device.id)
        .where(Schedule.id == schedule_id, Device.owner_id == current_user.id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Schedule not found")
    await db.delete(schedule)
