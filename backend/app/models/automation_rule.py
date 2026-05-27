from sqlalchemy import Integer, String, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AutomationRule(Base):
    __tablename__ = "automation_rules"

    id:           Mapped[int]         = mapped_column(Integer, primary_key=True)
    device_id:    Mapped[int]         = mapped_column(Integer, ForeignKey("devices.id"), nullable=False)
    trigger_type: Mapped[str]         = mapped_column(String(50), nullable=False)   # e.g. "power_above"
    condition:    Mapped[dict]        = mapped_column(JSON, nullable=False)          # {"threshold": 2000}
    action:       Mapped[dict]        = mapped_column(JSON, nullable=False)          # {"relay": 0, "state": false}
    enabled:      Mapped[bool]        = mapped_column(Boolean, default=True)

    device: Mapped["Device"] = relationship("Device", back_populates="rules")
