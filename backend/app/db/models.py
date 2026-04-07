import enum
import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class UserRole(str, enum.Enum):
    operator = "operator"
    supervisor = "supervisor"
    auditor = "auditor"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    full_name = Column(String(128), nullable=True)
    hashed_password = Column(String(256), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.operator)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    cases = relationship("Case", back_populates="created_by_user")
    evidence_items = relationship("EvidenceItem", back_populates="uploaded_by_user")
    custody_events = relationship("CustodyEvent", back_populates="actor_user")


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    legal_basis = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    closed_at = Column(DateTime(timezone=True), nullable=True)

    created_by_user = relationship("User", back_populates="cases")
    evidence_items = relationship("EvidenceItem", back_populates="case")
    custody_events = relationship("CustodyEvent", back_populates="case")


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    original_filename = Column(String(512), nullable=False)
    mime_type = Column(String(128), nullable=True)
    size_bytes = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False, index=True)
    storage_key = Column(String(512), nullable=False)  # MinIO object key
    source_description = Column(Text, nullable=True)
    tool_name = Column(String(128), nullable=True)
    tool_version = Column(String(64), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    acquired_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    case = relationship("Case", back_populates="evidence_items")
    uploaded_by_user = relationship("User", back_populates="evidence_items")
    custody_events = relationship("CustodyEvent", back_populates="evidence_item")


class CustodyEvent(Base):
    """Append-only audit log with hash chaining to detect tampering."""

    __tablename__ = "custody_events"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    evidence_item_id = Column(Integer, ForeignKey("evidence_items.id"), nullable=True)
    action = Column(String(64), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    actor_role = Column(String(32), nullable=False)
    timestamp_utc = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    source_ip = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)

    # Hash chaining fields
    prev_event_hash = Column(String(64), nullable=True)
    event_hash = Column(String(64), nullable=False)

    case = relationship("Case", back_populates="custody_events")
    evidence_item = relationship("EvidenceItem", back_populates="custody_events")
    actor_user = relationship("User", back_populates="custody_events")


def compute_event_hash(event_data: dict) -> str:
    """Compute SHA-256 of a custody event's canonical JSON representation."""
    canonical = json.dumps(event_data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()
