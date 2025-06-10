from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
from app.enums.user_role import Role
from app.models.property import Property


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(Enum(Role), default=Role.USER)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_blocked = Column(Boolean, default=False)

    properties = relationship("Property", back_populates="owner")
    bookings = relationship("Booking", back_populates="user")