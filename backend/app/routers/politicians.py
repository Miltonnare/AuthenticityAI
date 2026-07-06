from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from app.core.database import get_db
from app.core.security import RoleChecker
from app.models.politician import Politician
from app.models.contradiction import Claim
from app.models.speech import Speech
from app.schemas.politician import PoliticianCreate, PoliticianOut, PoliticianUpdate
from app.schemas.contradiction import ClaimOut

router = APIRouter(prefix="/politicians", tags=["Politicians"])
is_staff = RoleChecker(allowed_roles=["admin", "journalist"])

@router.get("", response_model=List[PoliticianOut])
def list_politicians(
    q: Optional[str] = None, 
    party: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    query = db.query(Politician)
    if q:
        query = query.filter(
            (Politician.first_name.ilike(f"%{q}%")) | 
            (Politician.last_name.ilike(f"%{q}%"))
        )
    if party:
        query = query.filter(Politician.party.ilike(party))
    return query.offset(skip).limit(limit).all()

@router.post("", response_model=PoliticianOut, status_code=status.HTTP_201_CREATED)
def create_politician(
    politician_in: PoliticianCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(is_staff)
):
    new_politician = Politician(**politician_in.model_dump())
    db.add(new_politician)
    db.commit()
    db.refresh(new_politician)
    return new_politician

@router.get("/{id}", response_model=PoliticianOut)
def get_politician(id: UUID, db: Session = Depends(get_db)):
    politician = db.query(Politician).filter(Politician.id == id).first()
    if not politician:
        raise HTTPException(status_code=404, detail="Politician not found")
    return politician

@router.get("/{id}/timeline", response_model=List[ClaimOut])
def get_politician_timeline(id: UUID, db: Session = Depends(get_db)):
    # Verify politician exists
    politician = db.query(Politician).filter(Politician.id == id).first()
    if not politician:
        raise HTTPException(status_code=404, detail="Politician not found")
    
    # Retrieve claims sorted by speech date
    claims = db.query(Claim).join(Speech).filter(
        Claim.politician_id == id
    ).order_by(Speech.date_delivered.desc()).all()
    
    return claims
