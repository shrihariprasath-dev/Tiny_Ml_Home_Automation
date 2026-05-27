from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user, hash_password
from app.models.device import Device
from app.models.user import User
from app.schemas.device import DeviceCreate, DeviceRead, RelayCommand
import aiomqtt, json, ssl
from app.core.config import get_settings

router = APIRouter(prefix="/api/devices", tags=["devices"])
settings = get_settings()


async def _publish_relay_cmd(device_id: str, cmd: RelayCommand) -> None:
    tls_ctx = ssl.create_default_context(cafile=settings.mqtt_ca_cert) \
              if settings.mqtt_tls else None
    try:
        async with aiomqtt.Client(
            hostname=settings.mqtt_host, port=settings.mqtt_port,
            username=settings.mqtt_username, password=settings.mqtt_password,
            tls_context=tls_ctx,
        ) as client:
            topic = f"home/{device_id}/cmd/relay"
            payload = json.dumps({"relay": cmd.relay, "state": cmd.state})
            await client.publish(topic, payload, qos=1)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"MQTT error: {exc}")


@router.get("", response_model=list[DeviceRead])
async def list_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Device).where(Device.owner_id == current_user.id)
    )
    return result.scalars().all()


@router.post("", response_model=DeviceRead, status_code=201)
async def register_device(
    body: DeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Device).where(Device.device_id == body.device_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="device_id already registered")

    device = Device(
        device_id=body.device_id,
        name=body.name,
        room=body.room,
        owner_id=current_user.id,
        secret_hash=hash_password(body.secret),
    )
    db.add(device)
    await db.flush()
    return device


@router.get("/{device_id}", response_model=DeviceRead)
async def get_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Device).where(Device.id == device_id,
                             Device.owner_id == current_user.id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.put("/{device_id}/relay")
async def control_relay(
    device_id: int,
    cmd: RelayCommand,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Device).where(Device.id == device_id,
                             Device.owner_id == current_user.id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if cmd.relay not in range(4):
        raise HTTPException(status_code=422, detail="relay must be 0–3")

    await _publish_relay_cmd(device.device_id, cmd)
    return {"ok": True, "relay": cmd.relay, "state": cmd.state}


@router.delete("/{device_id}", status_code=204)
async def delete_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Device).where(Device.id == device_id,
                             Device.owner_id == current_user.id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    await db.delete(device)
