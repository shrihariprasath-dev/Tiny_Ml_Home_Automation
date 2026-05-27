from sqlalchemy import Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id:            Mapped[int]      = mapped_column(Integer, primary_key=True)
    email:         Mapped[str]      = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str]      = mapped_column(String(255), nullable=False)
    role:          Mapped[str]      = mapped_column(String(20), default="user")   # admin / user / viewer
    created_at:    Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    devices:  Mapped[list["Device"]] = relationship("Device", back_populates="owner", lazy="selectin")
    rooms:    Mapped[list["Room"]]   = relationship("Room",   back_populates="owner", lazy="selectin")
