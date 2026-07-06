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
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SpeechDetailOut(SpeechOut):
    segments: List[TranscriptSegmentOut] = []

    class Config:
        from_attributes = True
