from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "Smart Home API"
    app_version: str = "1.0.0"
    debug: bool = False

    # PostgreSQL
    postgres_url: str = "postgresql+asyncpg://smarthome:smarthome@postgres:5432/smarthome"

    # InfluxDB
    influx_url: str = "http://influxdb:8086"
    influx_token: str = "smarthome-token"
    influx_org: str = "smarthome"
    influx_bucket: str = "energy_telemetry"
    influx_bucket_hourly: str = "energy_hourly"
    influx_bucket_daily: str = "energy_daily"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # MQTT
    mqtt_host: str = "mosquitto"
    mqtt_port: int = 8883
    mqtt_tls: bool = True
    mqtt_username: str = "backend"
    mqtt_password: str = "backend_secret"
    mqtt_ca_cert: str = "/certs/ca.crt"

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 7

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # AI service
    ai_service_url: str = "http://ai_service:8001"

    # OTA
    ota_firmware_path: str = "/firmware"


@lru_cache
def get_settings() -> Settings:
    return Settings()
