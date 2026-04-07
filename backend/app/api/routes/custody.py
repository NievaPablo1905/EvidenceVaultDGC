"""Chain-of-custody / audit log endpoints."""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.models import CustodyEvent, User, UserRole
from app.db.session import get_db
from app.schemas.custody import CustodyEventRead
from app.services.audit import verify_chain

router = APIRouter(prefix="/custody", tags=["custody"])

_READ_ROLES = (UserRole.supervisor, UserRole.auditor, UserRole.admin)


@router.get(
    "/",
    response_model=List[CustodyEventRead],
    summary="List all custody events (supervisors, auditors, admins)",
)
def list_custody_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_READ_ROLES)),
    skip: int = 0,
    limit: int = 100,
) -> list[CustodyEvent]:
    return (
        db.query(CustodyEvent)
        .order_by(CustodyEvent.id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get(
    "/verify",
    summary="Verify chain integrity (auditors, admins)",
)
def verify_custody_chain(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.auditor, UserRole.admin)),
) -> dict:
    errors = verify_chain(db)
    total = db.query(CustodyEvent).count()
    return {
        "total_events": total,
        "errors": errors,
        "chain_intact": len(errors) == 0,
    }
