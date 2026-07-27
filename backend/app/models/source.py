import uuid
from sqlalchemy import Column, String, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class Source(Base):
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    classification = Column(String(50), default="unverified", nullable=False) # 'official', 'reputable_press', 'unverified'
    base_score = Column(Numeric(3, 2), default=0.60, nullable=False)
    website_url = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
