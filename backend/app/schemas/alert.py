from pydantic import BaseModel
from datetime import datetime


class AlertCreate(BaseModel):
    device_id: int
    type: str
    severity: str
    message: str


class AlertRead(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    device_id: int
    type: str
    severity: str
    message: str
    created_at: datetime
    acknowledged_at: datetime | None


class ScheduleCreate(BaseModel):
    device_id: int
    cron_expr: str
    action: dict
    enabled: bool = True


class ScheduleRead(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    device_id: int
    cron_expr: str
    action: dict
    enabled: bool
