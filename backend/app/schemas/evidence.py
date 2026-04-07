from datetime import datetime

from pydantic import BaseModel


class EvidenceRead(BaseModel):
    id: int
    case_id: int
    original_filename: str
    mime_type: str | None
    size_bytes: int
    sha256: str
    source_description: str | None
    tool_name: str | None
    tool_version: str | None
    uploaded_by: int
    acquired_at: datetime

    model_config = {"from_attributes": True}
