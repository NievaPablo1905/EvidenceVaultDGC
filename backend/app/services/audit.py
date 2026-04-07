"""Chain-of-custody audit service.

Every custody event is linked to the previous event's hash so that any
tampering with historical records can be detected by recomputing the chain.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import CustodyEvent, compute_event_hash


# Actions ─────────────────────────────────────────────────────────────────────
ACTION_CREATE_CASE = "CREATE_CASE"
ACTION_INGEST_EVIDENCE = "INGEST_EVIDENCE"
ACTION_DOWNLOAD_EVIDENCE = "DOWNLOAD_EVIDENCE"
ACTION_LIST_EVIDENCE = "LIST_EVIDENCE"
ACTION_CREATE_USER = "CREATE_USER"
ACTION_BOOTSTRAP_ADMIN = "BOOTSTRAP_ADMIN"
ACTION_LOGIN = "LOGIN"


def _get_last_event_hash(db: Session) -> str | None:
    last = (
        db.query(CustodyEvent)
        .order_by(CustodyEvent.id.desc())
        .first()
    )
    return last.event_hash if last else None


def append_custody_event(
    db: Session,
    *,
    action: str,
    actor_id: int,
    actor_role: str,
    case_id: int | None = None,
    evidence_item_id: int | None = None,
    source_ip: str | None = None,
    notes: str | None = None,
) -> CustodyEvent:
    prev_hash = _get_last_event_hash(db)
    timestamp = datetime.now(timezone.utc)

    event_data = {
        "action": action,
        "actor_id": actor_id,
        "actor_role": actor_role,
        "case_id": case_id,
        "evidence_item_id": evidence_item_id,
        "timestamp_utc": timestamp.isoformat(),
        "source_ip": source_ip,
        "notes": notes,
        "prev_event_hash": prev_hash,
    }
    event_hash = compute_event_hash(event_data)

    event = CustodyEvent(
        case_id=case_id,
        evidence_item_id=evidence_item_id,
        action=action,
        actor_id=actor_id,
        actor_role=actor_role,
        timestamp_utc=timestamp,
        source_ip=source_ip,
        notes=notes,
        prev_event_hash=prev_hash,
        event_hash=event_hash,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def verify_chain(db: Session) -> list[dict]:
    """Walk the entire custody chain and report any broken links."""
    events = db.query(CustodyEvent).order_by(CustodyEvent.id.asc()).all()
    errors = []
    prev_hash: str | None = None

    for ev in events:
        if ev.prev_event_hash != prev_hash:
            errors.append(
                {
                    "event_id": ev.id,
                    "expected_prev": prev_hash,
                    "stored_prev": ev.prev_event_hash,
                    "error": "prev_event_hash mismatch",
                }
            )

        expected_data = {
            "action": ev.action,
            "actor_id": ev.actor_id,
            "actor_role": ev.actor_role,
            "case_id": ev.case_id,
            "evidence_item_id": ev.evidence_item_id,
            "timestamp_utc": ev.timestamp_utc.isoformat(),
            "source_ip": ev.source_ip,
            "notes": ev.notes,
            "prev_event_hash": ev.prev_event_hash,
        }
        expected_hash = compute_event_hash(expected_data)
        if expected_hash != ev.event_hash:
            errors.append(
                {
                    "event_id": ev.id,
                    "error": "event_hash mismatch — record may have been tampered with",
                }
            )

        prev_hash = ev.event_hash

    return errors
