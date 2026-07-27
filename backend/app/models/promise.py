import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Date, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Promise(Base):
    __tablename__ = "promises"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    politician_id = Column(UUID(as_uuid=True), ForeignKey("politicians.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="proposed", nullable=False)
    category = Column(String(100), nullable=False)
    target_completion_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    politician = relationship("Politician")
    evidence = relationship("PromiseEvidence", back_populates="promise", cascade="all, delete-orphan")

class PromiseEvidence(Base):
    __tablename__ = "promise_evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    promise_id = Column(UUID(as_uuid=True), ForeignKey("promises.id", ondelete="CASCADE"), nullable=False)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="SET NULL"), nullable=True)
    evidence_type = Column(String(50), nullable=False) # 'statement', 'bill_vote', 'department_report'
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    promise = relationship("Promise", back_populates="evidence")
    claim = relationship("Claim")
