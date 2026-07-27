import uuid
from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Integer, Numeric, Text, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Speech(Base):
    __tablename__ = "speeches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    politician_id = Column(UUID(as_uuid=True), ForeignKey("politicians.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(512), nullable=False)
    source_url = Column(String(512))
    media_type = Column(String(50), nullable=False) # 'youtube', 'mp4', 'manual'
    status = Column(String(50), nullable=False, default="pending") # 'pending', 'processing', 'completed', 'failed'
    date_delivered = Column(Date, nullable=False, index=True)
    
    # Media metadata additions for Speech Ingestion Pipeline
    file_size_bytes = Column(BigInteger, nullable=True)
    duration_seconds = Column(Numeric(8, 2), nullable=True)
    audio_codec = Column(String(50), nullable=True)
    download_speed_kbps = Column(Numeric(8, 2), nullable=True)
    error_log = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    politician = relationship("Politician", back_populates="speeches")
    segments = relationship("TranscriptSegment", back_populates="speech", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="speech", cascade="all, delete-orphan")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    speech_id = Column(UUID(as_uuid=True), ForeignKey("speeches.id", ondelete="CASCADE"), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    start_time = Column(Numeric(8, 2), nullable=False) # in seconds
    end_time = Column(Numeric(8, 2), nullable=False)
    text_content = Column(Text, nullable=False)

    # Relationships
    speech = relationship("Speech", back_populates="segments")
    claims = relationship("Claim", back_populates="segment")
