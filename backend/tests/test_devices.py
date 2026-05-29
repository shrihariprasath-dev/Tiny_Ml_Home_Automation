"""
Device endpoint tests — CRUD, relay control, auth enforcement.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from .conftest import get_token


_DEVICE_PAYLOAD = {
    "device_id": "esp32_living_01",
    "name":      "Living Room Node",
    "room":      "living_room",
    "secret":    "device_secret_abc",
}


# ── Auth guard ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_devices_requires_auth(client):
    resp = await client.get("/api/devices")
    assert resp.status_code == 401


# ── CRUD ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_device(auth_client):
    resp = await auth_client.post("/api/devices", json=_DEVICE_PAYLOAD)
    assert resp.status_code == 201
    body = resp.json()
    assert body["device_id"] == "esp32_living_01"
    assert body["name"] == "Living Room Node"
    assert "secret" not in body
    assert "secret_hash" not in body


@pytest.mark.asyncio
async def test_list_devices_returns_list(auth_client):
    await auth_client.post("/api/devices", json={**_DEVICE_PAYLOAD, "device_id": "esp32_list_01"})
    resp = await auth_client.get("/api/devices")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_device_by_id(auth_client):
    create = await auth_client.post("/api/devices", json={
        **_DEVICE_PAYLOAD, "device_id": "esp32_get_01"
    })
    device_id = create.json()["device_id"]

    resp = await auth_client.get(f"/api/devices/{device_id}")
    assert resp.status_code == 200
    assert resp.json()["device_id"] == device_id


@pytest.mark.asyncio
async def test_get_nonexistent_device(auth_client):
    resp = await auth_client.get("/api/devices/does_not_exist")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_device_rejected(auth_client):
    payload = {**_DEVICE_PAYLOAD, "device_id": "esp32_dup_01"}
    await auth_client.post("/api/devices", json=payload)
    resp = await auth_client.post("/api/devices", json=payload)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_delete_device(auth_client):
    create = await auth_client.post("/api/devices", json={
        **_DEVICE_PAYLOAD, "device_id": "esp32_del_01"
    })
    device_id = create.json()["device_id"]

    del_resp = await auth_client.delete(f"/api/devices/{device_id}")
    assert del_resp.status_code == 204

    get_resp = await auth_client.get(f"/api/devices/{device_id}")
    assert get_resp.status_code == 404


# ── Relay control ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_relay_control(auth_client):
    create = await auth_client.post("/api/devices", json={
        **_DEVICE_PAYLOAD, "device_id": "esp32_relay_01"
    })
    device_id = create.json()["device_id"]

    resp = await auth_client.put(f"/api/devices/{device_id}/relay",
                                  json={"relay": 0, "state": True})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_relay_invalid_index(auth_client):
    create = await auth_client.post("/api/devices", json={
        **_DEVICE_PAYLOAD, "device_id": "esp32_relay_02"
    })
    device_id = create.json()["device_id"]

    resp = await auth_client.put(f"/api/devices/{device_id}/relay",
                                  json={"relay": 99, "state": True})
    assert resp.status_code == 422


# ── Ownership isolation ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_device_not_visible_to_other_user(app_instance):
    async with AsyncClient(
        transport=ASGITransport(app=app_instance), base_url="http://test"
    ) as c:
        token_a = await get_token(c, "owner_a@test.com")
        token_b = await get_token(c, "owner_b@test.com")

        # User A registers a device
        c.headers["Authorization"] = f"Bearer {token_a}"
        create = await c.post("/api/devices", json={
            **_DEVICE_PAYLOAD, "device_id": "esp32_private_01"
        })
        device_id = create.json()["device_id"]

        # User B should not see User A's device
        c.headers["Authorization"] = f"Bearer {token_b}"
        resp = await c.get(f"/api/devices/{device_id}")
        assert resp.status_code == 404
