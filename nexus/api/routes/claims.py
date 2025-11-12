"""Claims API routes"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from nexus.storage.postgres import PostgresStore

router = APIRouter()
store = PostgresStore()


class ClaimResponse(BaseModel):
    id: UUID
    claim_text: str
    claim_type: Optional[str]
    polarity: Optional[str]
    magnitude: Optional[float]
    confidence: Optional[float]


@router.get("/", response_model=List[ClaimResponse])
async def list_claims(
    company_id: Optional[UUID] = None,
    evidence_id: Optional[UUID] = None,
    claim_type: Optional[str] = None,
    limit: int = 100
):
    """List claims with optional filters"""
    conditions = []
    params = {"limit": limit}
    
    if company_id:
        conditions.append("company_id = :company_id")
        params["company_id"] = str(company_id)
    
    if evidence_id:
        conditions.append("evidence_id = :evidence_id")
        params["evidence_id"] = str(evidence_id)
    
    if claim_type:
        conditions.append("claim_type = :claim_type")
        params["claim_type"] = claim_type
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
        SELECT id, claim_text, claim_type, polarity, magnitude, confidence
        FROM claims
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT :limit
    """
    results = store.fetch_all(query, params)
    
    return [
        ClaimResponse(
            id=row[0],
            claim_text=row[1],
            claim_type=row[2],
            polarity=row[3],
            magnitude=row[4],
            confidence=row[5]
        )
        for row in results
    ]


@router.get("/{claim_id}")
async def get_claim(claim_id: UUID):
    """Get claim details"""
    query = """
        SELECT c.id, c.claim_text, c.claim_type, c.polarity, c.magnitude, 
               c.confidence, c.extracted_entities, c.model_version, c.created_at,
               c.evidence_id, c.company_id
        FROM claims c
        WHERE c.id = :id
    """
    result = store.fetch_one(query, {"id": str(claim_id)})
    
    if not result:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    return {
        "id": result[0],
        "claim_text": result[1],
        "claim_type": result[2],
        "polarity": result[3],
        "magnitude": result[4],
        "confidence": result[5],
        "extracted_entities": result[6],
        "model_version": result[7],
        "created_at": result[8].isoformat() if result[8] else None,
        "evidence_id": result[9],
        "company_id": result[10]
    }


@router.get("/hypothesis/{hypothesis_id}")
async def get_hypothesis_claims(hypothesis_id: UUID, limit: int = 100):
    """Get claims linked to a hypothesis"""
    query = """
        SELECT c.id, c.claim_text, c.claim_type, c.polarity, c.magnitude, 
               c.confidence, hc.relevance_score, hc.impact_direction
        FROM claims c
        JOIN hypothesis_claims hc ON c.id = hc.claim_id
        WHERE hc.hypothesis_id = :hypothesis_id
        ORDER BY hc.relevance_score DESC
        LIMIT :limit
    """
    results = store.fetch_all(query, {"hypothesis_id": str(hypothesis_id), "limit": limit})
    
    return [
        {
            "id": row[0],
            "claim_text": row[1],
            "claim_type": row[2],
            "polarity": row[3],
            "magnitude": row[4],
            "confidence": row[5],
            "relevance_score": row[6],
            "impact_direction": row[7]
        }
        for row in results
    ]
