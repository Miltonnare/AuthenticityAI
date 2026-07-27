from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from app.core.database import get_db
from app.models.promise import Promise, PromiseEvidence
from app.schemas.promise import PromiseCreate, PromiseOut, PromiseEvidenceCreate, PromiseEvidenceOut
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/promises", tags=["promises"])

@router.post("", response_model=PromiseOut, status_code=status.HTTP_201_CREATED)
def create_promise(
    promise_in: PromiseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "journalist"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    promise = Promise(
        politician_id=promise_in.politician_id,
        title=promise_in.title,
        description=promise_in.description,
        category=promise_in.category,
        target_completion_date=promise_in.target_completion_date
    )
    db.add(promise)
    db.commit()
    db.refresh(promise)
    return promise

@router.get("", response_model=List[PromiseOut])
def list_promises(
    politician_id: Optional[UUID] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Promise)
    if politician_id:
        query = query.filter(Promise.politician_id == politician_id)
    if status:
        query = query.filter(Promise.status == status)
    if category:
        query = query.filter(Promise.category == category)
    return query.all()

@router.post("/evidence", response_model=PromiseEvidenceOut, status_code=status.HTTP_201_CREATED)
def create_evidence(
    evidence_in: PromiseEvidenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "journalist"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    promise = db.query(Promise).filter(Promise.id == evidence_in.promise_id).first()
    if not promise:
        raise HTTPException(status_code=404, detail="Promise not found")
    
    evidence = PromiseEvidence(
        promise_id=evidence_in.promise_id,
        claim_id=evidence_in.claim_id,
        evidence_type=evidence_in.evidence_type,
        notes=evidence_in.notes
    )
    db.add(evidence)
    
    old_status = promise.status
    # State Machine checks: adjust promise status based on evidence tags
    if evidence_in.evidence_type == "opposing_statement" or (evidence_in.notes and "contradicts" in evidence_in.notes.lower()):
        promise.status = "broken"
    elif evidence_in.evidence_type == "supporting_vote" or (evidence_in.notes and "supports" in evidence_in.notes.lower()):
        promise.status = "in_progress"
    
    if promise.status != old_status:
        try:
            from app.models.subscription import Subscription, Notification
            subs = db.query(Subscription).filter(Subscription.politician_id == promise.politician_id).all()
            for sub in subs:
                n = Notification(
                    user_id=sub.user_id,
                    title="Promise Status Changed",
                    body=f"Promise '{promise.title}' status shifted from {old_status} to {promise.status}.",
                    is_read=False
                )
                db.add(n)
        except Exception as e:
            pass
            
    db.commit()
    db.refresh(evidence)
    return evidence
