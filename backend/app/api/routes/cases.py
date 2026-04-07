from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, require_roles
from app.db.models import Case, User, UserRole
from app.db.session import get_db
from app.schemas.case import CaseCreate, CaseRead
from app.services import audit

router = APIRouter(prefix="/cases", tags=["cases"])

# Operators, supervisors, and admins can create/view cases.
# Auditors can view but not create.
_WRITE_ROLES = (UserRole.operator, UserRole.supervisor, UserRole.admin)
_READ_ROLES = (UserRole.operator, UserRole.supervisor, UserRole.auditor, UserRole.admin)


@router.post(
    "/",
    response_model=CaseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new case",
)
def create_case(
    payload: CaseCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_WRITE_ROLES)),
) -> Case:
    case = Case(
        title=payload.title,
        description=payload.description,
        legal_basis=payload.legal_basis,
        created_by=current_user.id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    audit.append_custody_event(
        db,
        action=audit.ACTION_CREATE_CASE,
        actor_id=current_user.id,
        actor_role=current_user.role.value,
        case_id=case.id,
        source_ip=get_client_ip(request),
        notes=f"Case '{case.title}' created",
    )

    return case


@router.get("/", response_model=List[CaseRead], summary="List all cases")
def list_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_READ_ROLES)),
) -> list[Case]:
    return db.query(Case).order_by(Case.created_at.desc()).all()


@router.get("/{case_id}", response_model=CaseRead, summary="Get a single case")
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_READ_ROLES)),
) -> Case:
    case = db.query(Case).filter(Case.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return case
