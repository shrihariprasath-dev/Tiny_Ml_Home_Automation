from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Room(Base):
    __tablename__ = "rooms"

    id:       Mapped[int] = mapped_column(Integer, primary_key=True)
    name:     Mapped[str] = mapped_column(String(100), nullable=False)
    floor:    Mapped[str] = mapped_column(String(50),  nullable=True)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    owner:   Mapped["User"]          = relationship("User",   back_populates="rooms")
    devices: Mapped[list["Device"]]  = relationship("Device", back_populates="room_rel", lazy="selectin")
