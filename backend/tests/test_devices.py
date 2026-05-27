import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


async def _get_token(client, email="dev@example.com", password="devpass"):
    await client.post("/auth/register", json={"email": email, "password": password})
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


@pytest.fixture
async def auth_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        token = await _get_token(c)
        c.headers.update({"Authorization": f"Bearer {token}"})
        yield c


@pytest.mark.asyncio
async def test_register_device(auth_client):
    resp = await auth_client.post("/api/devices", json={
        "device_id": "esp32_test_01",
        "name": "Living Room",
        "room": "living_room",
        "secret": "device_secret_xyz",
    })
    assert resp.status_code == 201
    assert resp.json()["device_id"] == "esp32_test_01"


@pytest.mark.asyncio
async def test_list_devices(auth_client):
    resp = await auth_client.get("/api/devices")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_duplicate_device_rejected(auth_client):
    payload = {"device_id": "esp32_dup", "name": "A", "secret": "s"}
    await auth_client.post("/api/devices", json=payload)
    resp = await auth_client.post("/api/devices", json=payload)
    assert resp.status_code == 400
