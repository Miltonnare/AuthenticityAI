from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class FeedbackReportCreate(BaseModel):
    target_id: UUID
    target_type: str
    report_type: str
    description: str

class FeedbackReportOut(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    target_id: UUID
    target_type: str
    report_type: str
    description: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
