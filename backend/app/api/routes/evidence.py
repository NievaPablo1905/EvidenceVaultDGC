"""Evidence ingest and download endpoints."""
import hashlib
import io
import uuid
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, require_roles
from app.db.models import Case, EvidenceItem, User, UserRole
from app.db.session import get_db
from app.schemas.evidence import EvidenceRead
from app.services import audit, storage

router = APIRouter(prefix="/cases/{case_id}/evidence", tags=["evidence"])

_WRITE_ROLES = (UserRole.operator, UserRole.supervisor, UserRole.admin)
_READ_ROLES = (UserRole.operator, UserRole.supervisor, UserRole.auditor, UserRole.admin)

CHUNK_SIZE = 64 * 1024  # 64 KB streaming chunks


@router.post(
    "/",
    response_model=EvidenceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload evidence file to a case",
)
async def upload_evidence(
    case_id: int,
    request: Request,
    file: UploadFile = File(..., description="Evidence file to upload"),
    source_description: str = Form(default=None),
    tool_name: str = Form(default=None),
    tool_version: str = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_WRITE_ROLES)),
) -> EvidenceItem:
    _get_case_or_404(case_id, db)

    # Stream file, compute SHA-256 and buffer in memory
    sha256_digest = hashlib.sha256()
    buffer = io.BytesIO()
    size = 0

    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        sha256_digest.update(chunk)
        buffer.write(chunk)
        size += len(chunk)

    sha256_hex = sha256_digest.hexdigest()
    object_key = f"{case_id}/{uuid.uuid4().hex}-{file.filename}"
    buffer.seek(0)

    try:
        storage.upload_evidence(
            object_key,
            buffer,
            size,
            file.content_type or "application/octet-stream",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Storage upload failed: {exc}",
        ) from exc

    item = EvidenceItem(
        case_id=case_id,
        original_filename=file.filename or "unknown",
        mime_type=file.content_type,
        size_bytes=size,
        sha256=sha256_hex,
        storage_key=object_key,
        source_description=source_description,
        tool_name=tool_name,
        tool_version=tool_version,
        uploaded_by=current_user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    audit.append_custody_event(
        db,
        action=audit.ACTION_INGEST_EVIDENCE,
        actor_id=current_user.id,
        actor_role=current_user.role.value,
        case_id=case_id,
        evidence_item_id=item.id,
        source_ip=get_client_ip(request),
        notes=f"Ingested '{file.filename}' SHA-256={sha256_hex} size={size}B",
    )

    return item


@router.get("/", response_model=List[EvidenceRead], summary="List evidence items in a case")
def list_evidence(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_READ_ROLES)),
) -> list[EvidenceItem]:
    _get_case_or_404(case_id, db)
    return (
        db.query(EvidenceItem)
        .filter(EvidenceItem.case_id == case_id)
        .order_by(EvidenceItem.acquired_at.desc())
        .all()
    )


@router.get(
    "/{evidence_id}",
    response_model=EvidenceRead,
    summary="Get evidence item metadata",
)
def get_evidence(
    case_id: int,
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_READ_ROLES)),
) -> EvidenceItem:
    return _get_item_or_404(case_id, evidence_id, db)


@router.get(
    "/{evidence_id}/download",
    summary="Download evidence file (logs custody event)",
)
def download_evidence(
    case_id: int,
    evidence_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_READ_ROLES)),
) -> StreamingResponse:
    item = _get_item_or_404(case_id, evidence_id, db)

    try:
        stream, _size, content_type = storage.download_evidence(item.storage_key)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Storage download failed: {exc}",
        ) from exc

    audit.append_custody_event(
        db,
        action=audit.ACTION_DOWNLOAD_EVIDENCE,
        actor_id=current_user.id,
        actor_role=current_user.role.value,
        case_id=case_id,
        evidence_item_id=item.id,
        source_ip=get_client_ip(request),
        notes=f"Downloaded '{item.original_filename}' SHA-256={item.sha256}",
    )

    return StreamingResponse(
        content=stream,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{item.original_filename}"',
            "X-Evidence-SHA256": item.sha256,
        },
    )


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_case_or_404(case_id: int, db: Session) -> Case:
    case = db.query(Case).filter(Case.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return case


def _get_item_or_404(case_id: int, evidence_id: int, db: Session) -> EvidenceItem:
    item = (
        db.query(EvidenceItem)
        .filter(EvidenceItem.id == evidence_id, EvidenceItem.case_id == case_id)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    return item
