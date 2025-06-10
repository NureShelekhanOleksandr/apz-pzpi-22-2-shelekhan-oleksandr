from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AccessCodeBase(BaseModel):
    code: str
    is_used: bool = False
    user_id: int


class AccessCodeCreate(AccessCodeBase):
    pass


class AccessCodeUpdate(BaseModel):
    code: Optional[str] = None
    is_used: Optional[bool] = None
    user_id: Optional[int] = None


class AccessCode(AccessCodeBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True
