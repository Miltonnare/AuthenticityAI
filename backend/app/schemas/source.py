from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class SourceCreate(BaseModel):
    name: str
    classification: str
    base_score: float
    website_url: Optional[str] = None

class SourceOut(BaseModel):
    id: UUID
    name: str
    classification: str
    base_score: float
    website_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
