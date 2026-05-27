"""
ota.py — OTA firmware management endpoints.

GET  /ota/version          returns latest release metadata (polled by ESP32)
POST /ota/release          admin uploads new firmware .bin + version string
GET  /ota/firmware/{ver}   download firmware binary
"""

import hashlib
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_admin
from app.models.ota_release import OtaRelease

router = APIRouter(prefix="/ota", tags=["OTA"])

FIRMWARE_DIR = Path("firmware_store")
FIRMWARE_DIR.mkdir(exist_ok=True)


@router.get("/version")
async def get_latest_version(db: AsyncSession = Depends(get_db)):
    """Return the latest OTA release record. Called by ESP32 ota_task every hour."""
    result = await db.execute(
        select(OtaRelease)
        .order_by(OtaRelease.released_at.desc())
        .limit(1)
    )
    release = result.scalar_one_or_none()
    if not release:
        raise HTTPException(404, "No firmware releases found")
    return {
        "version":      release.version,
        "firmware_url": release.firmware_url,
        "checksum":     release.checksum,
        "released_at":  release.released_at.isoformat(),
    }


@router.post("/release", dependencies=[Depends(require_admin)])
async def create_release(
    version:  str                  = Form(...),
    file:     UploadFile            = File(...),
    db:       AsyncSession          = Depends(get_db),
):
    """Upload a new firmware .bin. Admin only."""
    content = await file.read()
    sha256  = hashlib.sha256(content).hexdigest()

    dest = FIRMWARE_DIR / f"firmware_{version}.bin"
    dest.write_bytes(content)

    url = f"/ota/firmware/{version}"

    release = OtaRelease(
        version=version,
        firmware_url=url,
        checksum=sha256,
    )
    db.add(release)
    await db.commit()
    await db.refresh(release)

    return {
        "id":           release.id,
        "version":      version,
        "firmware_url": url,
        "checksum":     sha256,
        "size_bytes":   len(content),
    }


@router.get("/firmware/{version}")
async def download_firmware(version: str):
    """Serve firmware binary. Used by esp_https_ota() on the ESP32."""
    path = FIRMWARE_DIR / f"firmware_{version}.bin"
    if not path.exists():
        raise HTTPException(404, f"Firmware {version} not found")
    return FileResponse(
        path=str(path),
        media_type="application/octet-stream",
        filename=f"firmware_{version}.bin",
    )
