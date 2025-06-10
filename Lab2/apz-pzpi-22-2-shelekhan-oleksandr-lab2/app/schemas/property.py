from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class PropertyBase(BaseModel):
    name: str
    description: Optional[str]
    rooms: int
    price: float
    location: Optional[str]


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(PropertyBase):
    name: Optional[str] = None
    description: Optional[str] = None
    rooms: Optional[int] = None
    price: Optional[float] = None
    location: Optional[str] = None


class Property(PropertyBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True
        from_attributes = True


class AvailabilityPeriod(BaseModel):
    start_date: date
    end_date: date


class PropertyWithAvailabilityPeriods(Property):
    availability_periods: List[AvailabilityPeriod]