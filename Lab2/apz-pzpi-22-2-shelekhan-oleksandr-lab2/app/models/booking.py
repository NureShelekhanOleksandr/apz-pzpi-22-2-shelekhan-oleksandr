from datetime import datetime
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.enums.booking_status import BookingStatus


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)

    property = relationship("Property", back_populates="bookings", lazy="selectin")
    user = relationship("User", back_populates="bookings", lazy="selectin")
