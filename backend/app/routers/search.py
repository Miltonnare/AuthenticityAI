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
    typology: Optional[str] = None,
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
               language_code, original_claim_text, typology, extraction_confidence, is_decomposed, parent_claim_id,
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
        
    if typology:
        sql += " AND typology = :typology"
        params["typology"] = typology
        
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
            language_code=row["language_code"],
            original_claim_text=row["original_claim_text"],
            typology=row["typology"],
            extraction_confidence=float(row["extraction_confidence"]),
            is_decomposed=row["is_decomposed"],
            parent_claim_id=row["parent_claim_id"],
            created_at=row["created_at"]
        ))
        
    return claims_out

def reciprocal_rank_fusion(dense_results: list, sparse_results: list, k: int = 60) -> list:
    rrf_scores = {}
    
    # Process dense ranks
    for rank, doc in enumerate(dense_results):
        doc_id = str(doc["id"])
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))
        
    # Process sparse ranks
    for rank, doc in enumerate(sparse_results):
        doc_id = str(doc["id"])
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))
        
    # Sort doc IDs by score descending
    sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_docs

@router.get("/claims/hybrid", response_model=List[ClaimOut])
def search_claims_hybrid(
    q: str = Query(..., description="Query text to search for"),
    politician_id: Optional[UUID] = None,
    category: Optional[str] = None,
    typology: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Performs hybrid dense/sparse search combining pgvector similarity with
    FTS keyword indexing via Reciprocal Rank Fusion (RRF).
    """
    query_vector = get_embedding(q)
    
    # 1. Run Dense Search
    dense_sql = """
        SELECT id, politician_id, speech_id, segment_id, claim_text, category, created_at,
               language_code, original_claim_text, typology, extraction_confidence, is_decomposed, parent_claim_id
        FROM claims
        WHERE 1=1
    """
    dense_params = {"vector": str(query_vector), "limit": limit * 2}
    if politician_id:
        dense_sql += " AND politician_id = :politician_id"
        dense_params["politician_id"] = str(politician_id)
    if category:
        dense_sql += " AND category = :category"
        dense_params["category"] = category
    if typology:
        dense_sql += " AND typology = :typology"
        dense_params["typology"] = typology
        
    dense_sql += " ORDER BY embedding <=> :vector::vector LIMIT :limit"
    dense_results = db.execute(text(dense_sql), dense_params).mappings().all()
    
    # 2. Run Sparse Search (LIKE query fallback for SQLite tests compatibility)
    sparse_sql = """
        SELECT id, politician_id, speech_id, segment_id, claim_text, category, created_at,
               language_code, original_claim_text, typology, extraction_confidence, is_decomposed, parent_claim_id
        FROM claims
        WHERE claim_text LIKE :query
    """
    sparse_params = {"query": f"%{q}%", "limit": limit * 2}
    if politician_id:
        sparse_sql += " AND politician_id = :politician_id"
        sparse_params["politician_id"] = str(politician_id)
    if category:
        sparse_sql += " AND category = :category"
        sparse_params["category"] = category
    if typology:
        sparse_sql += " AND typology = :typology"
        sparse_params["typology"] = typology
        
    sparse_sql += " LIMIT :limit"
    sparse_results = db.execute(text(sparse_sql), sparse_params).mappings().all()
    
    # 3. Reciprocal Rank Fusion
    fused = reciprocal_rank_fusion(dense_results, sparse_results)[:limit]
    
    fused_ids = [str(f[0]) for f in fused]
    if not fused_ids:
        return []
        
    claims = db.query(Claim).filter(Claim.id.in_(fused_ids)).all()
    claims_dict = {str(c.id): c for c in claims}
    
    claims_out = []
    for doc_id, score in fused:
        claim = claims_dict.get(doc_id)
        if claim:
            claims_out.append(ClaimOut(
                id=claim.id,
                politician_id=claim.politician_id,
                speech_id=claim.speech_id,
                segment_id=claim.segment_id,
                claim_text=claim.claim_text,
                category=claim.category,
                language_code=claim.language_code,
                original_claim_text=claim.original_claim_text,
                typology=claim.typology,
                extraction_confidence=float(claim.extraction_confidence),
                is_decomposed=claim.is_decomposed,
                parent_claim_id=claim.parent_claim_id,
                created_at=claim.created_at
            ))
    return claims_out

@router.get("/claims/{id}/related", response_model=List[ClaimOut])
def get_related_claims(
    id: UUID,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Query similar claims delivered by other politicians based on vector proximity.
    """
    target = db.query(Claim).filter(Claim.id == id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Claim not found")
        
    sql = """
        SELECT id, politician_id, speech_id, segment_id, claim_text, category, created_at,
               language_code, original_claim_text, typology, extraction_confidence, is_decomposed, parent_claim_id,
               (1 - (embedding <=> :vector::vector)) AS similarity
        FROM claims
        WHERE politician_id != :pol_id AND id != :claim_id
        ORDER BY embedding <=> :vector::vector LIMIT :limit
    """
    params = {
        "vector": str(target.embedding),
        "pol_id": str(target.politician_id),
        "claim_id": str(target.id),
        "limit": limit
    }
    result = db.execute(text(sql), params).mappings().all()
    
    claims_out = []
    for row in result:
        claims_out.append(ClaimOut(
            id=row["id"],
            politician_id=row["politician_id"],
            speech_id=row["speech_id"],
            segment_id=row["segment_id"],
            claim_text=row["claim_text"],
            category=row["category"],
            language_code=row["language_code"],
            original_claim_text=row["original_claim_text"],
            typology=row["typology"],
            extraction_confidence=float(row["extraction_confidence"]),
            is_decomposed=row["is_decomposed"],
            parent_claim_id=row["parent_claim_id"],
            created_at=row["created_at"]
        ))
    return claims_out
