from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(String, nullable=False)
    type = Column(String, default="info")  # e.g., 'info', 'success', 'error', 'warning'
    created_at = Column(DateTime, default=datetime.utcnow)
    read = Column(Boolean, default=False)

    user = relationship("User", back_populates="notifications")
