from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.core.database import get_db
from app.models.feedback import FeedbackReport
from app.models.contradiction import Contradiction
from app.schemas.feedback import FeedbackReportCreate, FeedbackReportOut
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="", tags=["User Feedback Loops"])

@router.post("/feedback", response_model=FeedbackReportOut, status_code=status.HTTP_201_CREATED)
def create_feedback_report(
    report_in: FeedbackReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if report_in.target_type not in ["claim", "segment", "contradiction"]:
        raise HTTPException(status_code=400, detail="Invalid target type")
        
    report = FeedbackReport(
        user_id=current_user.id,
        target_id=report_in.target_id,
        target_type=report_in.target_type,
        report_type=report_in.report_type,
        description=report_in.description,
        status="open"
    )
    db.add(report)
    db.commit()
    
    if report_in.target_type == "contradiction" and report_in.report_type == "verification_challenge":
        count = db.query(FeedbackReport).filter(
            FeedbackReport.target_id == report_in.target_id,
            FeedbackReport.target_type == "contradiction",
            FeedbackReport.report_type == "verification_challenge",
            FeedbackReport.status == "open"
        ).count()
        
        if count >= 5:
            contra = db.query(Contradiction).filter(Contradiction.id == report_in.target_id).first()
            if contra:
                contra.review_status = "pending_review"
                db.commit()
                
    db.refresh(report)
    return report

@router.get("/admin/feedback/queue", response_model=List[FeedbackReportOut])
def list_feedback_reports(
    status: str = "open",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "journalist"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
        
    return db.query(FeedbackReport).filter(
        FeedbackReport.status == status
    ).order_by(FeedbackReport.created_at.desc()).all()
