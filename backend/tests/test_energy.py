"""
Energy endpoint tests — auth guards, response schema, history range.
InfluxDB is mocked in conftest.py so no live time-series DB is needed.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from .conftest import get_token


# ── Auth guards ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_realtime_requires_auth(client):
    resp = await client.get("/api/energy/realtime")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_history_requires_auth(client):
    resp = await client.get("/api/energy/history")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_summary_requires_auth(client):
    resp = await client.get("/api/energy/summary")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_rooms_requires_auth(client):
    resp = await client.get("/api/energy/rooms")
    assert resp.status_code == 401


# ── Response schema with mocked InfluxDB ──────────────────────────────────────

def _mock_influx_record(device_id="esp32_room_01", power_w=500.0):
    record = MagicMock()
    record.values = {
        "device_id": device_id,
        "room":      "living_room",
    }
    record.get_field.return_value    = "power_w"
    record.get_value.return_value    = power_w
    record.get_time.return_value     = MagicMock(isoformat=lambda: "2026-05-29T12:00:00Z")
    return record


@pytest.mark.asyncio
async def test_realtime_returns_list(auth_client):
    mock_table  = MagicMock()
    mock_table.records = [_mock_influx_record()]
    mock_query  = AsyncMock(return_value=[mock_table])

    with patch("app.services.influx_client.get_influx_client") as mock_client:
        mock_client.return_value.query_api.return_value.query = mock_query
        resp = await auth_client.get("/api/energy/realtime")

    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_history_accepts_time_range(auth_client):
    with patch("app.services.influx_client.get_influx_client") as mock_client:
        mock_client.return_value.query_api.return_value.query = AsyncMock(return_value=[])
        resp = await auth_client.get(
            "/api/energy/history",
            params={"from": "2026-05-01T00:00:00Z", "to": "2026-05-29T00:00:00Z"},
        )

    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_summary_returns_period_data(auth_client):
    with patch("app.services.influx_client.get_influx_client") as mock_client:
        mock_client.return_value.query_api.return_value.query = AsyncMock(return_value=[])
        resp = await auth_client.get("/api/energy/summary", params={"period": "daily"})

    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_rooms_returns_breakdown(auth_client):
    with patch("app.services.influx_client.get_influx_client") as mock_client:
        mock_client.return_value.query_api.return_value.query = AsyncMock(return_value=[])
        resp = await auth_client.get("/api/energy/rooms")

    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ── Health (no auth) ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_endpoint(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert "version" in resp.json()
