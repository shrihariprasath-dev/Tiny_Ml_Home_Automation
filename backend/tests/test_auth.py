"""
Auth endpoint tests — register, login, refresh, edge cases.
"""

import pytest
from httpx import AsyncClient, ASGITransport


# ── Register ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_success(client):
    resp = await client.post("/auth/register", json={
        "email":    "newuser@example.com",
        "password": "SecurePass1!",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "newuser@example.com"
    assert "password" not in body
    assert "password_hash" not in body


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "Pass1234!"}
    await client.post("/auth/register", json=payload)
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_register_invalid_email(client):
    resp = await client.post("/auth/register", json={
        "email":    "not-an-email",
        "password": "Pass1234!",
    })
    assert resp.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(client):
    await client.post("/auth/register", json={
        "email": "login_ok@example.com", "password": "Pass1234!"
    })
    resp = await client.post("/auth/login", json={
        "email": "login_ok@example.com", "password": "Pass1234!"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token"  in body
    assert "refresh_token" in body
    assert body.get("token_type") == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/auth/register", json={
        "email": "wrongpass@example.com", "password": "Correct1!"
    })
    resp = await client.post("/auth/login", json={
        "email": "wrongpass@example.com", "password": "WrongPass!"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client):
    resp = await client.post("/auth/login", json={
        "email": "ghost@nowhere.com", "password": "anything"
    })
    assert resp.status_code == 401


# ── Token refresh ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_refresh_token_success(client):
    await client.post("/auth/register", json={
        "email": "refresh_user@example.com", "password": "Pass1234!"
    })
    login = await client.post("/auth/login", json={
        "email": "refresh_user@example.com", "password": "Pass1234!"
    })
    refresh_token = login.json()["refresh_token"]

    resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_refresh_with_invalid_token(client):
    resp = await client.post("/auth/refresh", json={"refresh_token": "garbage.token.value"})
    assert resp.status_code in (401, 422)


# ── Protected route requires token ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_protected_route_without_token(client):
    resp = await client.get("/api/devices")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_with_bad_token(client):
    resp = await client.get("/api/devices",
                            headers={"Authorization": "Bearer faketoken"})
    assert resp.status_code == 401
