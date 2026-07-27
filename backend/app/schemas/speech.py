from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, date
from typing import Optional, List

class TranscriptSegmentOut(BaseModel):
    id: UUID
    speech_id: UUID
    sequence_number: int
    start_time: float
    end_time: float
    text_content: str
    language_code: Optional[str] = "en"
    translated_text: Optional[str] = None

    class Config:
        from_attributes = True

class SpeechBase(BaseModel):
    title: str
    source_url: Optional[str] = None
    media_type: str # 'youtube', 'mp4', 'manual'
    date_delivered: date

class SpeechCreate(SpeechBase):
    politician_id: UUID

class SpeechOut(SpeechBase):
    id: UUID
    politician_id: UUID
    status: str
    file_size_bytes: Optional[int] = None
    duration_seconds: Optional[float] = None
    audio_codec: Optional[str] = None
    download_speed_kbps: Optional[float] = None
    error_log: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SpeechDetailOut(SpeechOut):
    segments: List[TranscriptSegmentOut] = []

    class Config:
        from_attributes = True
