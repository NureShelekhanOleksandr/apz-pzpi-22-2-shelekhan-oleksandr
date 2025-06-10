from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Enum, Float
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.enums.payment import PaymentStatus


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)

    # user = relationship("User", back_populates="payments")
    # booking = relationship("Booking", back_populates="payment")
