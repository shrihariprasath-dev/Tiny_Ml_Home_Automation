from pydantic import BaseModel
from datetime import datetime


class TelemetryPayload(BaseModel):
    device_id: str
    ts: int
    voltage: float
    current: float
    power_w: float
    power_factor: float
    energy_kwh: float
    temperature: float
    humidity: float
    motion: bool
    relay_states: list[bool]
    anomaly_score: float = 0.0
    occupancy_prob: float = 0.0
    firmware_version: str = "0.0.0"


class EnergyPoint(BaseModel):
    time: datetime
    power_w: float
    energy_kwh: float
    voltage: float
    current: float


class EnergySummary(BaseModel):
    device_id: str
    period: str
    total_kwh: float
    avg_power_w: float
    peak_power_w: float
    estimated_cost: float


class RoomEnergy(BaseModel):
    room: str
    total_kwh: float
    avg_power_w: float
    device_count: int
