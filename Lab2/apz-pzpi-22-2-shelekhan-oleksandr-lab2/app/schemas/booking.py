from pydantic import BaseModel
from typing import Optional
from pydantic.networks import EmailStr
from app.enums.booking_status import BookingStatus
from datetime import datetime, date
from app.schemas.property import Property


class BookingBase(BaseModel):
    property_id: int
    start_date: date
    end_date: date
    status: Optional[BookingStatus] = BookingStatus.PENDING


class BookingCreate(BookingBase):
    pass


class BookingUpdate(BaseModel):
    status: Optional[BookingStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class Booking(BookingBase):
    id: int
    created_at: datetime
    user_id: int

    class Config:
        orm_mode = True
        from_attributes = True


class PersonalizedOffer(BaseModel):
    property: Property
    discount: float
    message: str
