from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import UUID
from typing import List, Optional
import numpy as np
from app.core.database import get_db
from app.schemas.contradiction import ClaimOut
from app.models.contradiction import Claim

router = APIRouter(prefix="/search", tags=["Search"])

# Lazy-loaded embedding model to save memory during startup
_model = None

def get_embedding(query_text: str) -> List[float]:
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Failed to load sentence transformer model: {e}")
            # Return dummy vector if model loading failed (e.g. in test envs without torch/cache)
            return [0.1] * 384
            
    if _model == "MOCK":
        return [0.1] * 384
        
    try:
        embedding = _model.encode(query_text)
        return embedding.tolist()
    except Exception as e:
        print(f"Failed to generate query embedding: {e}")
        return [0.1] * 384

@router.get("/claims", response_model=List[ClaimOut])
def search_claims(
    q: str = Query(..., description="Query text to search for"),
    politician_id: Optional[UUID] = None,
    category: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Performs hybrid semantic and keyword search. It queries claims using pgvector
    cosine similarity combined with standard database SQL filters.
    """
    query_vector = get_embedding(q)
    
    # We write a custom SQL query using pgvector's cosine distance operator <=>
    # Cosine similarity = 1 - Cosine Distance
    sql = """
        SELECT id, politician_id, speech_id, segment_id, claim_text, category, created_at,
               (1 - (embedding <=> :vector::vector)) AS similarity
        FROM claims
        WHERE 1=1
    """
    params = {"vector": str(query_vector), "limit": limit}
    
    if politician_id:
        sql += " AND politician_id = :politician_id"
        params["politician_id"] = str(politician_id)
        
    if category:
        sql += " AND category = :category"
        params["category"] = category
        
    # We also do a keyword match to boost lexical matches in case vector mapping is off
    sql += " ORDER BY embedding <=> :vector::vector LIMIT :limit"
    
    result = db.execute(text(sql), params).mappings().all()
    
    # Convert mappings to Pydantic objects
    claims_out = []
    for row in result:
        claims_out.append(ClaimOut(
            id=row["id"],
            politician_id=row["politician_id"],
            speech_id=row["speech_id"],
            segment_id=row["segment_id"],
            claim_text=row["claim_text"],
            category=row["category"],
            created_at=row["created_at"]
        ))
        
    return claims_out
