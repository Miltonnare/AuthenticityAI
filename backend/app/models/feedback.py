import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class FeedbackReport(Base):
    __tablename__ = "feedback_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    target_id = Column(UUID(as_uuid=True), nullable=False)
    target_type = Column(String(50), nullable=False) # 'claim', 'segment', 'contradiction'
    report_type = Column(String(50), nullable=False) # 'typo_correction', 'context_omission', 'verification_challenge'
    description = Column(Text, nullable=False)
    status = Column(String(50), default="open", nullable=False) # 'open', 'applied', 'rejected'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
