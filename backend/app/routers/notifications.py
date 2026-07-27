from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.core.database import get_db
from app.models.subscription import Subscription, Notification
from app.models.politician import Politician
from app.schemas.subscription import NotificationOut
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["Notifications Registry"])

@router.post("/subscribe/{politician_id}", status_code=status.HTTP_200_OK)
def subscribe_to_politician(
    politician_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    politician = db.query(Politician).filter(Politician.id == politician_id).first()
    if not politician:
        raise HTTPException(status_code=404, detail="Politician not found")
        
    sub = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.politician_id == politician_id
    ).first()
    
    if sub:
        db.delete(sub)
        db.commit()
        return {"message": f"Successfully unsubscribed from alerts for {politician.first_name} {politician.last_name}."}
    
    new_sub = Subscription(
        user_id=current_user.id,
        politician_id=politician_id
    )
    db.add(new_sub)
    db.commit()
    return {"message": f"Successfully subscribed to alerts for {politician.first_name} {politician.last_name}."}

@router.get("", response_model=List[NotificationOut])
def get_user_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).all()

@router.post("/read-all", status_code=status.HTTP_200_OK)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True}, synchronize_session=False)
    db.commit()
    return {"message": "All notifications marked as read."}
