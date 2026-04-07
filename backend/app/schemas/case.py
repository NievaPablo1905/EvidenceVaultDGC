from datetime import datetime

from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    description: str | None = None
    legal_basis: str | None = None


class CaseRead(BaseModel):
    id: int
    title: str
    description: str | None
    legal_basis: str | None
    created_by: int
    created_at: datetime
    closed_at: datetime | None

    model_config = {"from_attributes": True}
