from sqlalchemy import Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from datetime import datetime


class Device(Base):
    __tablename__ = "devices"

    id:           Mapped[int]           = mapped_column(Integer, primary_key=True)
    device_id:    Mapped[str]           = mapped_column(String(64), unique=True, nullable=False, index=True)
    name:         Mapped[str]           = mapped_column(String(100), nullable=False)
    room:         Mapped[str | None]    = mapped_column(String(100), nullable=True)
    room_id:      Mapped[int | None]    = mapped_column(Integer, ForeignKey("rooms.id"), nullable=True)
    owner_id:     Mapped[int]           = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    secret_hash:  Mapped[str]           = mapped_column(String(255), nullable=False)
    firmware_ver: Mapped[str]           = mapped_column(String(20), default="0.0.0")
    created_at:   Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner:    Mapped["User"]                     = relationship("User",     back_populates="devices")
    room_rel: Mapped["Room | None"]              = relationship("Room",     back_populates="devices")
    alerts:   Mapped[list["Alert"]]              = relationship("Alert",    back_populates="device", lazy="selectin")
    schedules:Mapped[list["Schedule"]]           = relationship("Schedule", back_populates="device", lazy="selectin")
    rules:    Mapped[list["AutomationRule"]]     = relationship("AutomationRule", back_populates="device", lazy="selectin")
