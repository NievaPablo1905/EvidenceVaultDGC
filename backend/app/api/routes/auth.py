from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.db.models import User
from app.db.session import get_db
from app.schemas.token import Token
from app.services import audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token, summary="Obtain a JWT access token")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    user: User | None = db.query(User).filter(User.username == form_data.username).first()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    source_ip = request.client.host if request.client else None
    audit.append_custody_event(
        db,
        action=audit.ACTION_LOGIN,
        actor_id=user.id,
        actor_role=user.role.value,
        source_ip=source_ip,
        notes=f"User '{user.username}' logged in",
    )

    token = create_access_token(user.id)
    return Token(access_token=token)
