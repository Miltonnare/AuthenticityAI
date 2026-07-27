from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceOut
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/sources", tags=["Sources Registry"])

@router.post("", response_model=SourceOut, status_code=status.HTTP_201_CREATED)
def create_source(
    source_in: SourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "journalist"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    existing = db.query(Source).filter(Source.name == source_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Source name already exists")
        
    source = Source(
        name=source_in.name,
        classification=source_in.classification,
        base_score=source_in.base_score,
        website_url=source_in.website_url
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source

@router.get("", response_model=List[SourceOut])
def list_sources(db: Session = Depends(get_db)):
    return db.query(Source).all()
