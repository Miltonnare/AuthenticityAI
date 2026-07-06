from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from app.core.database import get_db
from app.core.security import RoleChecker
from app.models.speech import Speech
from app.models.politician import Politician
from app.schemas.speech import SpeechCreate, SpeechOut, SpeechDetailOut

router = APIRouter(prefix="/speeches", tags=["Speeches"])
is_staff = RoleChecker(allowed_roles=["admin", "journalist"])

@router.get("", response_model=List[SpeechOut])
def list_speeches(politician_id: Optional[UUID] = None, db: Session = Depends(get_db)):
    query = db.query(Speech)
    if politician_id:
        query = query.filter(Speech.politician_id == politician_id)
    return query.order_by(Speech.date_delivered.desc()).all()

@router.post("", response_model=SpeechOut, status_code=status.HTTP_201_CREATED)
def create_speech(
    speech_in: SpeechCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(is_staff)
):
    # Verify politician exists
    politician = db.query(Politician).filter(Politician.id == speech_in.politician_id).first()
    if not politician:
        raise HTTPException(status_code=404, detail="Politician not found")
        
    new_speech = Speech(**speech_in.model_dump(), status="pending")
    db.add(new_speech)
    db.commit()
    db.refresh(new_speech)
    
    # Enqueue Celery task for transcription and claim processing
    try:
        from app.worker.tasks import process_speech
        process_speech.delay(str(new_speech.id))
    except Exception as e:
        # Fallback or warning if celery is not connected
        print(f"Failed to enqueue background speech process: {e}")
        
    return new_speech

@router.get("/{id}", response_model=SpeechDetailOut)
def get_speech(id: UUID, db: Session = Depends(get_db)):
    speech = db.query(Speech).filter(Speech.id == id).first()
    if not speech:
        raise HTTPException(status_code=404, detail="Speech not found")
    return speech
