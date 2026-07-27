from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from datetime import datetime
import json
from app.core.database import get_db
from app.core.security import RoleChecker, get_current_user
from app.models.contradiction import Contradiction, AuditLog, Citation
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
        
    old_status = contradiction.review_status
    contradiction.review_status = review.review_status
    contradiction.reviewed_by = current_user.id
    contradiction.review_notes = review.review_notes
    
    if review.review_status == "verified":
        contradiction.verified_at = datetime.utcnow()
    
    # Save citations if provided
    citations_added = []
    if review.citations:
        # Clear existing citations if re-reviewing
        db.query(Citation).filter(Citation.contradiction_id == id).delete()
        for cit_in in review.citations:
            citation = Citation(
                contradiction_id=id,
                title=cit_in.title,
                url=cit_in.url,
                source_name=cit_in.source_name,
                published_date=cit_in.published_date
            )
            db.add(citation)
            citations_added.append({
                "title": cit_in.title,
                "url": cit_in.url,
                "source_name": cit_in.source_name
            })
            
    # Write Audit Log
    log_payload = {
        "old_status": old_status,
        "new_status": review.review_status,
        "review_notes": review.review_notes,
        "citations": citations_added
    }
    audit = AuditLog(
        user_id=current_user.id,
        action=f"{review.review_status}_contradiction",
        target_id=id,
        payload=json.dumps(log_payload)
    )
    db.add(audit)
    
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
