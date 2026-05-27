from sqlalchemy import Integer, String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id:        Mapped[int]  = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int]  = mapped_column(Integer, ForeignKey("devices.id"), nullable=False)
    cron_expr: Mapped[str]  = mapped_column(String(100), nullable=False)   # "0 22 * * *"
    action:    Mapped[dict] = mapped_column(JSON, nullable=False)           # {"relay": 0, "state": false}
    enabled:   Mapped[bool] = mapped_column(Boolean, default=True)

    device: Mapped["Device"] = relationship("Device", back_populates="schedules")
