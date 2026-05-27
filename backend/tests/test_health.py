"""
Minimal smoke test — verifies the FastAPI app imports cleanly and /health returns 200.
Requires no live database connection (mocks are injected below).
"""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_health_ok():
    with (
        patch("app.core.database.get_influx_client", return_value=AsyncMock()),
        patch("app.core.database.close_influx_client", new_callable=AsyncMock),
    ):
        from app.main import app  # noqa: E402 — imported inside patch context

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
