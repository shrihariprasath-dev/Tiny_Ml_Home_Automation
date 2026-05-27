"""
MQTT Bridge — subscribes to home/+/telemetry and home/+/alert,
writes telemetry to InfluxDB, persists alerts to PostgreSQL,
and triggers Celery alert tasks for threshold breaches.
"""
import asyncio
import json
import logging
import ssl
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.device import Device
from app.models.alert import Alert
from app.schemas.energy import TelemetryPayload
from app.services.influx_client import write_telemetry
from sqlalchemy import select

log = logging.getLogger(__name__)
settings = get_settings()

TELEMETRY_TOPIC = "home/+/telemetry"
ALERT_TOPIC     = "home/+/alert"
STATUS_TOPIC    = "home/+/status"


async def _handle_telemetry(topic: str, payload: bytes) -> None:
    try:
        data = json.loads(payload)
        reading = TelemetryPayload(**data)
        await write_telemetry(reading)

        # Update firmware version in PostgreSQL if changed
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Device).where(Device.device_id == reading.device_id)
            )
            device = result.scalar_one_or_none()
            if device and device.firmware_ver != reading.firmware_version:
                device.firmware_ver = reading.firmware_version
                await db.commit()

    except Exception as exc:
        log.error("Telemetry handler error: %s", exc)


async def _handle_alert(topic: str, payload: bytes) -> None:
    try:
        data = json.loads(payload)
        device_id_str = topic.split("/")[1]

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Device).where(Device.device_id == device_id_str)
            )
            device = result.scalar_one_or_none()
            if not device:
                log.warning("Alert from unknown device: %s", device_id_str)
                return

            alert = Alert(
                device_id=device.id,
                type=data.get("type", "anomaly"),
                severity=data.get("severity", "high"),
                message=json.dumps(data),
            )
            db.add(alert)
            await db.commit()
            log.info("Alert stored for device %s", device_id_str)

        # Dispatch Celery notification task
        from app.services.alert_engine import send_alert_notification
        send_alert_notification.delay(device_id_str, data)

    except Exception as exc:
        log.error("Alert handler error: %s", exc)


async def run_mqtt_bridge() -> None:
    """
    Async MQTT bridge using aiomqtt.
    Runs as a long-lived background task started from app lifespan.
    """
    import aiomqtt

    tls_ctx = None
    if settings.mqtt_tls:
        tls_ctx = ssl.create_default_context(cafile=settings.mqtt_ca_cert)

    reconnect_delay = 5
    while True:
        try:
            async with aiomqtt.Client(
                hostname=settings.mqtt_host,
                port=settings.mqtt_port,
                username=settings.mqtt_username,
                password=settings.mqtt_password,
                tls_context=tls_ctx,
            ) as client:
                log.info("MQTT bridge connected to %s:%d",
                         settings.mqtt_host, settings.mqtt_port)
                reconnect_delay = 5   # reset on successful connect

                await client.subscribe(TELEMETRY_TOPIC, qos=0)
                await client.subscribe(ALERT_TOPIC,     qos=2)
                await client.subscribe(STATUS_TOPIC,    qos=1)

                async for message in client.messages:
                    topic   = str(message.topic)
                    payload = message.payload

                    if "/telemetry" in topic:
                        await _handle_telemetry(topic, payload)
                    elif "/alert" in topic:
                        await _handle_alert(topic, payload)
                    elif "/status" in topic:
                        log.debug("Status update: %s → %s", topic, payload)

        except Exception as exc:
            log.error("MQTT bridge disconnected: %s — retry in %ds",
                      exc, reconnect_delay)
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, 60)   # cap at 60s
