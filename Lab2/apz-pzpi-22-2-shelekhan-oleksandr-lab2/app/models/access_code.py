from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from app.core.database import Base
from sqlalchemy.orm import relationship


class AccessCode(Base):
    __tablename__ = "access_codes"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(
        Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False
    )
    code = Column(String, nullable=False, unique=True)
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)

    # booking = relationship("Booking", back_populates="access_codes")
