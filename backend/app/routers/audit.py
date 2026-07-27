import hashlib
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.contradiction import AuditLog
from app.schemas.contradiction import AuditLogOut

router = APIRouter(prefix="/audit", tags=["Verifiable Audit Trails"])

@router.get("/logs", response_model=List[AuditLogOut])
def get_public_audit_logs(db: Session = Depends(get_db)):
    return db.query(AuditLog).order_by(AuditLog.created_at.asc()).all()

@router.get("/verify")
def verify_audit_trail_integrity(db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.asc()).all()
    
    current_prev = "0000000000000000000000000000000000000000000000000000000000000000"
    for idx, log in enumerate(logs):
        if log.prev_hash != current_prev:
            return {
                "is_valid": False,
                "tampered_log_id": str(log.id),
                "reason": f"Hash chain break at log index {idx}. Expected prev_hash {current_prev}, got {log.prev_hash}.",
                "total_records_checked": idx
            }
            
        hash_input = f"{log.prev_hash}{log.action}{log.payload}{log.target_id}"
        sig_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
        
        if log.signature_hash != sig_hash:
            return {
                "is_valid": False,
                "tampered_log_id": str(log.id),
                "reason": f"Signature mismatch at log index {idx}.",
                "total_records_checked": idx
            }
            
        current_prev = log.signature_hash
        
    return {
        "is_valid": True,
        "tampered_log_id": None,
        "reason": "Chain signature sequence checks out.",
        "total_records_checked": len(logs)
    }
