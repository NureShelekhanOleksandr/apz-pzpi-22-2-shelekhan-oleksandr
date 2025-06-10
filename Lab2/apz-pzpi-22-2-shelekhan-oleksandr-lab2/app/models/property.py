from sqlalchemy import Column, Integer, String, ForeignKey, Float, Text, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    rooms = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    location = Column(String, nullable=False)
    lock_id = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="properties", lazy="selectin")
    bookings = relationship("Booking", back_populates="property", lazy="selectin")
