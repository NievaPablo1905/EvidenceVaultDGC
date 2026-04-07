from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, get_current_user, require_roles
from app.db.models import User, UserRole
from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead
from app.core.security import hash_password
from app.services import audit

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user (admin only)",
)
def create_user(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin)),
) -> User:
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )
    user = User(
        username=payload.username,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    audit.append_custody_event(
        db,
        action=audit.ACTION_CREATE_USER,
        actor_id=current_user.id,
        actor_role=current_user.role.value,
        source_ip=get_client_ip(request),
        notes=f"Created user '{user.username}' with role '{user.role}'",
    )

    return user


@router.get("/me", response_model=UserRead, summary="Get current user info")
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
