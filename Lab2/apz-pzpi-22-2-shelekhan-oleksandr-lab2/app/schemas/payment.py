from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.enums.payment import PaymentStatus


class PaymentBase(BaseModel):
    booking_id: int
    amount: float
    status: PaymentStatus


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    amount: Optional[float] = None
    status: Optional[PaymentStatus] = None


class Payment(PaymentBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True

