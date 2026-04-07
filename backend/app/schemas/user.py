from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models import UserRole


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    full_name: str | None = None
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.operator


class UserRead(BaseModel):
    id: int
    username: str
    full_name: str | None
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
