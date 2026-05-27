from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"


class UserRead(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    email: str
    role: str
    created_at: datetime
