from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from datetime import date
import os
import shutil
from app.core.database import get_db
from app.core.security import RoleChecker
from app.models.speech import Speech
from app.models.politician import Politician
from app.schemas.speech import SpeechCreate, SpeechOut, SpeechDetailOut

router = APIRouter(prefix="/speeches", tags=["Speeches"])
is_staff = RoleChecker(allowed_roles=["admin", "journalist"])

TEMP_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_uploads")
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

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
    politician = db.query(Politician).filter(Politician.id == speech_in.politician_id).first()
    if not politician:
        raise HTTPException(status_code=404, detail="Politician not found")
        
    new_speech = Speech(**speech_in.model_dump(), status="pending")
    db.add(new_speech)
    db.commit()
    db.refresh(new_speech)
    
    try:
        from app.worker.tasks import process_speech
        process_speech.delay(str(new_speech.id))
    except Exception as e:
        print(f"Failed to enqueue background speech process: {e}")
        
    return new_speech

@router.post("/ingest/url", response_model=SpeechOut, status_code=status.HTTP_202_ACCEPTED)
def ingest_speech_url(
    speech_in: SpeechCreate,
    db: Session = Depends(get_db),
    current_user = Depends(is_staff)
):
    politician = db.query(Politician).filter(Politician.id == speech_in.politician_id).first()
    if not politician:
        raise HTTPException(status_code=404, detail="Politician not found")
        
    # Security Validation: Simple SSRF check (reject local hosts)
    url_lower = speech_in.source_url.lower() if speech_in.source_url else ""
    if "localhost" in url_lower or "127.0.0.1" in url_lower:
        raise HTTPException(status_code=400, detail="Invalid target URL configuration")

    new_speech = Speech(**speech_in.model_dump(), status="queued")
    db.add(new_speech)
    db.commit()
    db.refresh(new_speech)
    
    try:
        from app.worker.tasks import process_speech
        process_speech.delay(str(new_speech.id))
    except Exception as e:
        print(f"Failed to enqueue background url process: {e}")
        
    return new_speech

@router.post("/ingest/file", response_model=SpeechOut, status_code=status.HTTP_202_ACCEPTED)
def ingest_speech_file(
    file: UploadFile = File(...),
    politician_id: UUID = Form(...),
    title: str = Form(...),
    date_delivered: date = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(is_staff)
):
    politician = db.query(Politician).filter(Politician.id == politician_id).first()
    if not politician:
        raise HTTPException(status_code=404, detail="Politician not found")
        
    # File type validation
    allowed_types = ["video/mp4", "audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp3"]
    if file.content_type not in allowed_types:
        # Check by extension if content type header is omitted
        ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
        if ext not in [".mp4", ".mp3", ".wav"]:
            raise HTTPException(status_code=400, detail="Unsupported media format")

    # File size validation (limit 100MB)
    max_size = 100 * 1024 * 1024
    temp_file_path = os.path.join(TEMP_UPLOAD_DIR, f"{politician_id}_{file.filename}")
    
    size = 0
    try:
        with open(temp_file_path, "wb") as buffer:
            while True:
                chunk = file.file.read(8192)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_size:
                    raise HTTPException(status_code=413, detail="Payload too large. Limit is 100MB")
                buffer.write(chunk)
    except HTTPException:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise
    except Exception as e:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    new_speech = Speech(
        politician_id=politician_id,
        title=title,
        source_url=temp_file_path,
        media_type="mp4" if "mp4" in (file.content_type or "") else "manual",
        status="queued",
        date_delivered=date_delivered,
        file_size_bytes=size
    )
    db.add(new_speech)
    db.commit()
    db.refresh(new_speech)
    
    try:
        from app.worker.tasks import process_speech
        process_speech.delay(str(new_speech.id))
    except Exception as e:
        print(f"Failed to enqueue background file process: {e}")
        
    return new_speech

@router.get("/ingest/{id}/status")
def get_ingestion_status(id: UUID, db: Session = Depends(get_db)):
    speech = db.query(Speech).filter(Speech.id == id).first()
    if not speech:
        raise HTTPException(status_code=404, detail="Speech record not found")
        
    progress = 0.0
    details = "Waiting in queue"
    if speech.status == "queued":
        progress = 10.0
        details = "Queued for background worker"
    elif speech.status == "processing":
        progress = 50.0
        details = "Audio extraction and transcription processing"
    elif speech.status == "completed":
        progress = 100.0
        details = "Processing finished"
    elif speech.status == "failed":
        progress = 100.0
        details = "Processing failed"

    return {
        "speech_id": speech.id,
        "status": speech.status,
        "progress_percentage": progress,
        "details": details,
        "file_metadata": {
            "file_size_bytes": speech.file_size_bytes,
            "duration_seconds": float(speech.duration_seconds) if speech.duration_seconds else None,
            "audio_codec": speech.audio_codec
        }
    }

@router.get("/{id}", response_model=SpeechDetailOut)
def get_speech(id: UUID, db: Session = Depends(get_db)):
    speech = db.query(Speech).filter(Speech.id == id).first()
    if not speech:
        raise HTTPException(status_code=404, detail="Speech not found")
    return speech
