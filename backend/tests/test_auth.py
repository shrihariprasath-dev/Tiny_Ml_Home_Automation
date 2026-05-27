import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest.mark.asyncio
async def test_register_and_login(client):
    reg = await client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "testpass123",
    })
    assert reg.status_code == 201
    assert reg.json()["email"] == "test@example.com"

    login = await client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123",
    })
    assert login.status_code == 200
    tokens = login.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens


@pytest.mark.asyncio
async def test_login_invalid_password(client):
    resp = await client.post("/auth/login", json={
        "email": "nobody@example.com",
        "password": "wrong",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client):
    await client.post("/auth/register", json={
        "email": "refresh@example.com",
        "password": "pass",
    })
    login = await client.post("/auth/login", json={
        "email": "refresh@example.com",
        "password": "pass",
    })
    refresh_token = login.json()["refresh_token"]

    resp = await client.post("/auth/refresh",
                              json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
