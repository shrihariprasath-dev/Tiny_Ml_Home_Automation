"""
Shared pytest fixtures and async setup for all backend tests.

Uses httpx AsyncClient + ASGITransport so no live server is needed.
Database is an in-memory SQLite instance (aiosqlite) isolated per test session.
InfluxDB and MQTT are mocked at the dependency level.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport


# ── Patch external services before importing the app ──────────────────────────

@pytest.fixture(scope="session", autouse=True)
def _patch_externals():
    """Mock InfluxDB and MQTT so tests run without live services."""
    influx_mock = MagicMock()
    influx_mock.query_api.return_value = AsyncMock(query=AsyncMock(return_value=[]))
    influx_mock.write_api.return_value = MagicMock()

    with (
        patch("app.core.database.get_influx_client", return_value=influx_mock),
        patch("app.core.database.close_influx_client", new_callable=AsyncMock),
        patch("app.services.mqtt_bridge.run_mqtt_bridge", new_callable=AsyncMock),
        patch("aiomqtt.Client", MagicMock()),
    ):
        yield


# ── In-memory SQLite engine for tests ─────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def _use_sqlite():
    """Override DATABASE_URL to use in-memory SQLite instead of PostgreSQL."""
    with patch.dict("os.environ", {
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "SECRET_KEY":   "test-secret-key-not-for-production",
    }):
        yield


# ── App + table creation ───────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="session")
async def app_instance():
    from app.core.database import create_tables
    await create_tables()
    from app.main import app
    return app


# ── Unauthenticated client ─────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client(app_instance):
    async with AsyncClient(
        transport=ASGITransport(app=app_instance), base_url="http://test"
    ) as c:
        yield c


# ── Helper: register + login, return token ────────────────────────────────────

async def get_token(client: AsyncClient, email: str, password: str = "Passw0rd!") -> str:
    await client.post("/auth/register", json={"email": email, "password": password})
    resp = await client.post("/auth/login",    json={"email": email, "password": password})
    return resp.json().get("access_token", "")


# ── Authenticated client ───────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def auth_client(app_instance):
    async with AsyncClient(
        transport=ASGITransport(app=app_instance), base_url="http://test"
    ) as c:
        token = await get_token(c, "fixture_user@test.com")
        c.headers.update({"Authorization": f"Bearer {token}"})
        yield c
