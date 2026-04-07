from datetime import datetime

from pydantic import BaseModel


class CustodyEventRead(BaseModel):
    id: int
    case_id: int | None
    evidence_item_id: int | None
    action: str
    actor_id: int
    actor_role: str
    timestamp_utc: datetime
    source_ip: str | None
    notes: str | None
    prev_event_hash: str | None
    event_hash: str

    model_config = {"from_attributes": True}
