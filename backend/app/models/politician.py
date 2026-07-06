import uuid
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Politician(Base):
    __tablename__ = "politicians"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False, index=True)
    party = Column(String(100), nullable=False)
    current_office = Column(String(255))
    bio = Column(Text)
    image_url = Column(String(512))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    speeches = relationship("Speech", back_populates="politician", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="politician", cascade="all, delete-orphan")
