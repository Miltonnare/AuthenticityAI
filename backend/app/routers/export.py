import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
import hashlib
import secrets
from app.core.database import get_db
from app.models.api_key import APIKey
from app.models.politician import Politician
from app.models.contradiction import Claim
from app.schemas.api_key import APIKeyCreate, APIKeyOut, APIKeyNew
from app.routers.auth import get_current_user
from app.models.user import User
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/export", tags=["Data Export & API Keys"])

def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

@router.post("/api-keys", response_model=APIKeyNew, status_code=status.HTTP_201_CREATED)
def create_developer_api_key(
    key_in: APIKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    raw_key = "auth_live_" + secrets.token_urlsafe(32)
    hashed = hash_key(raw_key)
    
    api_key = APIKey(
        user_id=current_user.id,
        name=key_in.name,
        hashed_key=hashed,
        is_active=True
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    return APIKeyNew(
        id=api_key.id,
        name=api_key.name,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        api_key=raw_key
    )

@router.get("/api-keys", response_model=List[APIKeyOut])
def list_developer_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(APIKey).filter(APIKey.user_id == current_user.id).all()

@router.get("/politician/{id}")
def export_politician_dataset(
    id: UUID,
    format: str = Query("json", regex="^(json|csv)$"),
    db: Session = Depends(get_db)
):
    politician = db.query(Politician).filter(Politician.id == id).first()
    if not politician:
        raise HTTPException(status_code=404, detail="Politician not found")
        
    claims = db.query(Claim).filter(Claim.politician_id == id).all()
    
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["claim_id", "politician_id", "claim_text", "category", "typology", "created_at"])
        for claim in claims:
            writer.writerow([
                str(claim.id),
                str(claim.politician_id),
                claim.claim_text,
                claim.category,
                claim.typology,
                claim.created_at.isoformat() if claim.created_at else ""
            ])
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=politician_{id}_export.csv"}
        )
    else:
        export_data = {
            "politician": {
                "id": str(politician.id),
                "first_name": politician.first_name,
                "last_name": politician.last_name,
                "party": politician.party
            },
            "claims": [
                {
                    "id": str(c.id),
                    "claim_text": c.claim_text,
                    "category": c.category,
                    "typology": c.typology,
                    "created_at": c.created_at.isoformat() if c.created_at else ""
                } for c in claims
            ]
        }
        return export_data
