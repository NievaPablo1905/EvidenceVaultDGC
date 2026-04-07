"""DEV-ONLY bootstrap endpoint.

Creates the first admin user. MUST be disabled in production by setting
DEV_BOOTSTRAP_ENABLED=false in the environment.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.models import User, UserRole
from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead
from app.services import audit

router = APIRouter(prefix="/dev", tags=["dev"])


@router.post(
    "/bootstrap",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="[DEV ONLY] Create the first admin user",
    description=(
        "⚠️ **Development/lab endpoint only.** "
        "Disabled when `DEV_BOOTSTRAP_ENABLED=false`. "
        "Remove or restrict access before any production deployment."
    ),
)
def bootstrap_admin(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    if not settings.DEV_BOOTSTRAP_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bootstrap endpoint is disabled",
        )

    existing_admins = db.query(User).filter(User.role == UserRole.admin).count()
    if existing_admins > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An admin user already exists. Use normal user management.",
        )

    user = User(
        username=payload.username,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=UserRole.admin,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    audit.append_custody_event(
        db,
        action=audit.ACTION_BOOTSTRAP_ADMIN,
        actor_id=user.id,
        actor_role=user.role.value,
        notes=f"Bootstrap admin '{user.username}' created",
    )

    return user
