from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base


class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True, index=True)
    access_code_id = Column(Integer, ForeignKey("access_codes.id", ondelete="CASCADE"), nullable=False)
    accessed_at = Column(DateTime, default=datetime.utcnow)

    # access_code = relationship("AccessCode", back_populates="logs")
