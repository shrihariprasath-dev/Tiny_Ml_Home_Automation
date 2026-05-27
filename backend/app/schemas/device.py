from pydantic import BaseModel
from datetime import datetime


class DeviceCreate(BaseModel):
    device_id: str
    name: str
    room: str | None = None
    secret: str


class DeviceRead(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    device_id: str
    name: str
    room: str | None
    firmware_ver: str
    created_at: datetime


class RelayCommand(BaseModel):
    relay: int        # 0–3
    state: bool
