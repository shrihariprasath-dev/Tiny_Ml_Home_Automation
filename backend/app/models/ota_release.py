from sqlalchemy import Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from datetime import datetime


class OtaRelease(Base):
    __tablename__ = "ota_releases"

    id:           Mapped[int]      = mapped_column(Integer, primary_key=True)
    version:      Mapped[str]      = mapped_column(String(20),  nullable=False, unique=True)
    firmware_url: Mapped[str]      = mapped_column(String(500), nullable=False)
    checksum:     Mapped[str]      = mapped_column(String(64),  nullable=False)   # SHA-256 hex
    released_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
