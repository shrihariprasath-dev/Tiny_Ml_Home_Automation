from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from influxdb_client import Point, WriteOptions
from influxdb_client.client.write_api import ASYNCHRONOUS
from app.core.config import get_settings
from app.core.database import get_influx_client
from app.schemas.energy import TelemetryPayload, EnergyPoint, EnergySummary, RoomEnergy
from datetime import datetime, timezone
from typing import Any
import logging

log = logging.getLogger(__name__)
settings = get_settings()

COST_PER_KWH = 0.12   # USD — configurable via env in production


def _build_telemetry_point(payload: TelemetryPayload) -> Point:
    return (
        Point("energy_telemetry")
        .tag("device_id", payload.device_id)
        .field("voltage",        payload.voltage)
        .field("current",        payload.current)
        .field("power_w",        payload.power_w)
        .field("power_factor",   payload.power_factor)
        .field("energy_kwh",     payload.energy_kwh)
        .field("temperature",    payload.temperature)
        .field("humidity",       payload.humidity)
        .field("anomaly_score",  payload.anomaly_score)
        .field("occupancy_prob", payload.occupancy_prob)
        .field("motion",         int(payload.motion))
        .time(datetime.fromtimestamp(payload.ts, tz=timezone.utc))
    )


async def write_telemetry(payload: TelemetryPayload) -> None:
    client = get_influx_client()
    async with client.write_api() as write_api:
        point = _build_telemetry_point(payload)
        await write_api.write(bucket=settings.influx_bucket, record=point)


async def query_realtime(device_ids: list[str]) -> list[dict]:
    """Latest single reading per device."""
    client = get_influx_client()
    query_api = client.query_api()

    id_filter = " or ".join(f'r["device_id"] == "{d}"' for d in device_ids)
    flux = f"""
        from(bucket: "{settings.influx_bucket}")
          |> range(start: -5m)
          |> filter(fn: (r) => r._measurement == "energy_telemetry")
          |> filter(fn: (r) => {id_filter})
          |> last()
          |> pivot(rowKey:["_time","device_id"], columnKey:["_field"], valueColumn:"_value")
    """
    tables = await query_api.query(flux)
    results = []
    for table in tables:
        for record in table.records:
            results.append(record.values)
    return results


async def query_history(device_id: str,
                         start: datetime, stop: datetime) -> list[EnergyPoint]:
    client = get_influx_client()
    query_api = client.query_api()

    flux = f"""
        from(bucket: "{settings.influx_bucket}")
          |> range(start: {start.isoformat()}, stop: {stop.isoformat()})
          |> filter(fn: (r) => r._measurement == "energy_telemetry")
          |> filter(fn: (r) => r["device_id"] == "{device_id}")
          |> filter(fn: (r) => r._field == "power_w" or r._field == "energy_kwh"
                            or r._field == "voltage" or r._field == "current")
          |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
    """
    tables = await query_api.query(flux)
    points: list[EnergyPoint] = []
    for table in tables:
        for r in table.records:
            v = r.values
            points.append(EnergyPoint(
                time=v["_time"],
                power_w=v.get("power_w", 0),
                energy_kwh=v.get("energy_kwh", 0),
                voltage=v.get("voltage", 0),
                current=v.get("current", 0),
            ))
    return points


async def query_summary(device_id: str, period: str) -> EnergySummary:
    """period: 'daily' | 'monthly'"""
    client = get_influx_client()
    query_api = client.query_api()

    range_expr = "-1d" if period == "daily" else "-30d"
    flux = f"""
        from(bucket: "{settings.influx_bucket}")
          |> range(start: {range_expr})
          |> filter(fn: (r) => r._measurement == "energy_telemetry")
          |> filter(fn: (r) => r["device_id"] == "{device_id}")
          |> filter(fn: (r) => r._field == "power_w" or r._field == "energy_kwh")
          |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
    """
    tables = await query_api.query(flux)

    power_vals, kwh_vals = [], []
    for table in tables:
        for r in table.records:
            v = r.values
            if "power_w" in v:   power_vals.append(v["power_w"])
            if "energy_kwh" in v: kwh_vals.append(v["energy_kwh"])

    total_kwh   = max(kwh_vals) - min(kwh_vals) if len(kwh_vals) > 1 else 0
    avg_power   = sum(power_vals) / len(power_vals) if power_vals else 0
    peak_power  = max(power_vals) if power_vals else 0

    return EnergySummary(
        device_id=device_id,
        period=period,
        total_kwh=round(total_kwh, 4),
        avg_power_w=round(avg_power, 2),
        peak_power_w=round(peak_power, 2),
        estimated_cost=round(total_kwh * COST_PER_KWH, 4),
    )


async def query_room_breakdown(rooms: list[str]) -> list[RoomEnergy]:
    client = get_influx_client()
    query_api = client.query_api()

    results: list[RoomEnergy] = []
    for room in rooms:
        flux = f"""
            from(bucket: "{settings.influx_bucket}")
              |> range(start: -24h)
              |> filter(fn: (r) => r._measurement == "energy_telemetry")
              |> filter(fn: (r) => r["room"] == "{room}")
              |> filter(fn: (r) => r._field == "power_w")
              |> mean()
        """
        tables = await query_api.query(flux)
        power_vals = [r.values.get("_value", 0)
                      for t in tables for r in t.records]

        results.append(RoomEnergy(
            room=room,
            total_kwh=round(sum(power_vals) * 24 / 1000, 3),
            avg_power_w=round(sum(power_vals) / len(power_vals) if power_vals else 0, 2),
            device_count=len(power_vals),
        ))
    return results
