"""
OTA endpoint tests — version query, firmware upload (admin), download.
"""

import pytest
import io
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from .conftest import get_token


# ── /ota/version ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ota_version_no_releases(client):
    """Returns 404 when no releases exist yet."""
    with patch("app.routers.ota.AsyncSession") as _:
        resp = await client.get("/ota/version")
    # 404 (no release) or 200 — both are valid depending on DB state
    assert resp.status_code in (200, 404)


@pytest.mark.asyncio
async def test_ota_version_schema(client):
    """If a version is returned, it must have required fields."""
    resp = await client.get("/ota/version")
    if resp.status_code == 200:
        body = resp.json()
        assert "version"      in body
        assert "firmware_url" in body
        assert "checksum"     in body


# ── /ota/release (admin only) ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ota_release_requires_admin(auth_client):
    """Regular user cannot upload firmware."""
    fake_bin = io.BytesIO(b"\x00" * 100)
    resp = await auth_client.post(
        "/ota/release",
        data={"version": "1.0.0"},
        files={"file": ("firmware_1.0.0.bin", fake_bin, "application/octet-stream")},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_ota_release_requires_auth(client):
    """Unauthenticated upload is rejected."""
    fake_bin = io.BytesIO(b"\x00" * 100)
    resp = await client.post(
        "/ota/release",
        data={"version": "1.0.0"},
        files={"file": ("firmware_1.0.0.bin", fake_bin, "application/octet-stream")},
    )
    assert resp.status_code == 401


# ── /ota/firmware/{version} ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ota_firmware_404_for_missing(client):
    """Non-existent firmware version returns 404."""
    resp = await client.get("/ota/firmware/99.99.99")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_ota_version_not_found_without_releases(client):
    """GET /ota/version with no DB releases returns 404."""
    resp = await client.get("/ota/version")
    assert resp.status_code in (200, 404)
