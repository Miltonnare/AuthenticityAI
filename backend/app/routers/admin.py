from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.core.database import get_db
from app.core.security import RoleChecker, get_current_user
from app.models.contradiction import Contradiction
from app.models.speech import Speech
from app.models.user import User
from app.schemas.contradiction import ContradictionOut, ContradictionReview
from app.schemas.speech import SpeechOut

router = APIRouter(prefix="/admin", tags=["Admin Moderation"])

# Restrict all endpoints here to Admin or Journalist roles
is_moderator = RoleChecker(allowed_roles=["admin", "journalist"])

@router.get("/contradictions/queue", response_model=List[ContradictionOut])
def get_contradiction_queue(
    status: str = "pending_review", 
    db: Session = Depends(get_db),
    current_user: User = Depends(is_moderator)
):
    """
    Get the list of contradictions currently flagged and pending editorial review.
    """
    contradictions = db.query(Contradiction).filter(
        Contradiction.review_status == status
    ).order_by(Contradiction.created_at.desc()).all()
    return contradictions

@router.post("/contradictions/{id}/review", response_model=ContradictionOut)
def review_contradiction(
    id: UUID,
    review: ContradictionReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_moderator)
):
    """
    Approve/verify or dismiss a system-flagged contradiction.
    """
    contradiction = db.query(Contradiction).filter(Contradiction.id == id).first()
    if not contradiction:
        raise HTTPException(status_code=404, detail="Contradiction not found")
        
    contradiction.review_status = review.review_status
    contradiction.reviewed_by = current_user.id
    
    db.commit()
    db.refresh(contradiction)
    return contradiction

@router.get("/speeches/queue", response_model=List[SpeechOut])
def get_speech_processing_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(is_moderator)
):
    """
    Retrieve all speech ingestion jobs sorted by execution status.
    """
    speeches = db.query(Speech).order_by(Speech.created_at.desc()).all()
    return speeches
