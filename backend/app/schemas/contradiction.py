from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class ClaimOut(BaseModel):
    id: UUID
    politician_id: UUID
    speech_id: UUID
    segment_id: Optional[UUID] = None
    claim_text: str
    category: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ContradictionOut(BaseModel):
    id: UUID
    original_claim_id: UUID
    contradicting_claim_id: UUID
    original_claim: ClaimOut
    contradicting_claim: ClaimOut
    confidence_score: float
    explanation: str
    review_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ContradictionReview(BaseModel):
    review_status: str # 'verified', 'dismissed'
