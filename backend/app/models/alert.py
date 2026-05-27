from sqlalchemy import Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from datetime import datetime


class Alert(Base):
    __tablename__ = "alerts"

    id:              Mapped[int]            = mapped_column(Integer, primary_key=True)
    device_id:       Mapped[int]            = mapped_column(Integer, ForeignKey("devices.id"), nullable=False)
    type:            Mapped[str]            = mapped_column(String(50),  nullable=False)   # anomaly / threshold
    severity:        Mapped[str]            = mapped_column(String(20),  nullable=False)   # low / medium / high
    message:         Mapped[str]            = mapped_column(String(500), nullable=False)
    created_at:      Mapped[datetime]       = mapped_column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at: Mapped[datetime | None]= mapped_column(DateTime(timezone=True), nullable=True)

    device: Mapped["Device"] = relationship("Device", back_populates="alerts")
