from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, date
from typing import Optional, List
from app.schemas.contradiction import ClaimOut

class PromiseCreate(BaseModel):
    politician_id: UUID
    title: str
    description: str
    category: str
    target_completion_date: Optional[date] = None

class PromiseOut(BaseModel):
    id: UUID
    politician_id: UUID
    title: str
    description: str
    status: str
    category: str
    target_completion_date: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PromiseEvidenceCreate(BaseModel):
    promise_id: UUID
    claim_id: Optional[UUID] = None
    evidence_type: str
    notes: Optional[str] = None

class PromiseEvidenceOut(BaseModel):
    id: UUID
    promise_id: UUID
    claim_id: Optional[UUID] = None
    evidence_type: str
    notes: Optional[str] = None
    created_at: datetime
    claim: Optional[ClaimOut] = None

    class Config:
        from_attributes = True
