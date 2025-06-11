from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AccessCodeResponse(BaseModel):
    access_code: str
    valid_from: datetime
    valid_until: datetime
    booking_id: int


class AccessCodeCreate(BaseModel):
    valid_from: datetime
    valid_until: datetime


class AccessCode(BaseModel):
    id: int
    code: str
    valid_from: datetime
    valid_until: datetime
    booking_id: int

    class Config:
        orm_mode = True
        from_attributes = True