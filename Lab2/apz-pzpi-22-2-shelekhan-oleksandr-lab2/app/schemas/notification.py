from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NotificationBase(BaseModel):
    message: str
    type: str = "info"
    read: bool = False


class NotificationCreate(NotificationBase):
    user_id: int


class Notification(NotificationBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True
