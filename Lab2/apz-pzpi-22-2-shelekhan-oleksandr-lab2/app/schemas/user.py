from pydantic import BaseModel
from typing import Optional
from pydantic.networks import EmailStr
from app.enums.user_role import Role
from datetime import datetime


class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    role: Optional[Role] = Role.USER


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[Role] = None
    password: Optional[str] = None


class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class UserFull(User):
    password: str