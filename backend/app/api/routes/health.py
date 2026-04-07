from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.storage import get_minio_client

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", summary="Health check")
def health(db: Session = Depends(get_db)) -> dict:
    # Check DB
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    # Check MinIO
    minio_ok = False
    try:
        get_minio_client()
        minio_ok = True
    except Exception:
        pass

    return {
        "status": "ok" if (db_ok and minio_ok) else "degraded",
        "database": "ok" if db_ok else "error",
        "storage": "ok" if minio_ok else "error",
    }
