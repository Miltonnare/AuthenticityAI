from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, date
from typing import Optional, List

class ClaimOut(BaseModel):
    id: UUID
    politician_id: UUID
    speech_id: UUID
    segment_id: Optional[UUID] = None
    claim_text: str
    category: Optional[str] = None
    language_code: Optional[str] = "en"
    original_claim_text: Optional[str] = None
    typology: Optional[str] = "general"
    extraction_confidence: Optional[float] = 1.0
    is_decomposed: Optional[bool] = False
    parent_claim_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True

class CitationCreate(BaseModel):
    title: str
    url: str
    source_name: str
    published_date: Optional[date] = None


class CitationOut(BaseModel):
    id: UUID
    contradiction_id: UUID
    title: str
    url: str
    source_name: str
    published_date: Optional[date] = None
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
    reviewed_by: Optional[UUID] = None
    review_notes: Optional[str] = None
    verified_at: Optional[datetime] = None
    citations: Optional[List[CitationOut]] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContradictionReview(BaseModel):
    review_status: str # 'verified', 'dismissed'
    review_notes: Optional[str] = None
    citations: Optional[List[CitationCreate]] = []

class AuditLogOut(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    action: str
    target_id: UUID
    payload: Optional[str] = None
    prev_hash: Optional[str] = None
    signature_hash: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
