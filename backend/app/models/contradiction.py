import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Text, Boolean, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.core.database import Base

class Claim(Base):
    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    politician_id = Column(UUID(as_uuid=True), ForeignKey("politicians.id", ondelete="CASCADE"), nullable=False)
    speech_id = Column(UUID(as_uuid=True), ForeignKey("speeches.id", ondelete="CASCADE"), nullable=False)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("transcript_segments.id", ondelete="SET NULL"), nullable=True)
    claim_text = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=False) # matching all-MiniLM-L6-v2 vector dimension
    category = Column(String(100))
    
    # Multilingual fields
    language_code = Column(String(10), default="en", nullable=False)
    original_claim_text = Column(Text, nullable=True)
    
    # Advanced Claim Extraction fields
    typology = Column(String(50), default="general", nullable=False)
    extraction_confidence = Column(Numeric(5, 4), default=1.0000, nullable=False)
    is_decomposed = Column(Boolean, default=False, nullable=False)
    parent_claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    politician = relationship("Politician", back_populates="claims")
    speech = relationship("Speech", back_populates="claims")
    segment = relationship("TranscriptSegment", back_populates="claims")


class Contradiction(Base):
    __tablename__ = "contradictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    contradicting_claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    confidence_score = Column(Numeric(5, 4), nullable=False)
    explanation = Column(Text, nullable=False)
    review_status = Column(String(50), nullable=False, default="pending_review") # 'pending_review', 'verified', 'dismissed'
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_notes = Column(Text, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    original_claim = relationship("Claim", foreign_keys=[original_claim_id])
    contradicting_claim = relationship("Claim", foreign_keys=[contradicting_claim_id])
    reviewer = relationship("User")
    citations = relationship("Citation", back_populates="contradiction", cascade="all, delete-orphan")


class ClaimRevision(Base):
    __tablename__ = "claim_revisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    editor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    old_claim_text = Column(Text, nullable=False)
    new_claim_text = Column(Text, nullable=False)
    change_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    claim = relationship("Claim")
    editor = relationship("User")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False) # 'verify_contradiction', 'dismiss_contradiction', 'edit_claim'
    target_id = Column(UUID(as_uuid=True), nullable=False)
    payload = Column(Text, nullable=True) # JSON dump of what changed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")


class Citation(Base):
    __tablename__ = "citations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contradiction_id = Column(UUID(as_uuid=True), ForeignKey("contradictions.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    url = Column(String(512), nullable=False)
    source_name = Column(String(100), nullable=False)
    published_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    contradiction = relationship("Contradiction", back_populates="citations")
