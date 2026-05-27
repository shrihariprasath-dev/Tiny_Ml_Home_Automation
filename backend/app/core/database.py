from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from app.core.config import get_settings
from typing import AsyncGenerator

settings = get_settings()

# ── PostgreSQL ────────────────────────────────────────────────────────────────

engine = create_async_engine(
    settings.postgres_url,
    pool_size=10,
    max_overflow=20,
    echo=settings.debug,
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ── InfluxDB ──────────────────────────────────────────────────────────────────

_influx_client: InfluxDBClientAsync | None = None


def get_influx_client() -> InfluxDBClientAsync:
    global _influx_client
    if _influx_client is None:
        _influx_client = InfluxDBClientAsync(
            url=settings.influx_url,
            token=settings.influx_token,
            org=settings.influx_org,
        )
    return _influx_client


async def close_influx_client() -> None:
    global _influx_client
    if _influx_client:
        await _influx_client.close()
        _influx_client = None
