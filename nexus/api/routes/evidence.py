"""Evidence API routes"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from nexus.storage.postgres import PostgresStore

router = APIRouter()
store = PostgresStore()


class EvidenceResponse(BaseModel):
    id: UUID
    source_type: str
    title: str
    source_date: str
    validation_status: str


@router.get("/", response_model=List[EvidenceResponse])
async def list_evidence(source_type: str = None, limit: int = 100):
    """List evidence"""
    if source_type:
        query = """
            SELECT id, source_type, title, source_date, validation_status
            FROM evidence
            WHERE source_type = :source_type
            ORDER BY created_at DESC
            LIMIT :limit
        """
        results = store.fetch_all(query, {"source_type": source_type, "limit": limit})
    else:
        query = """
            SELECT id, source_type, title, source_date, validation_status
            FROM evidence
            ORDER BY created_at DESC
            LIMIT :limit
        """
        results = store.fetch_all(query, {"limit": limit})
    
    return [
        EvidenceResponse(
            id=row[0],
            source_type=row[1],
            title=row[2] or "",
            source_date=row[3].isoformat() if row[3] else "",
            validation_status=row[4]
        )
        for row in results
    ]


@router.get("/{evidence_id}")
async def get_evidence(evidence_id: UUID):
    """Get evidence details"""
    query = """
        SELECT id, source_type, title, content, source_date, source_url,
               validation_status, created_at
        FROM evidence
        WHERE id = :id
    """
    result = store.fetch_one(query, {"id": str(evidence_id)})
    
    if not result:
        raise HTTPException(status_code=404, detail="Evidence not found")
    
    return {
        "id": result[0],
        "source_type": result[1],
        "title": result[2],
        "content": result[3][:1000],  # First 1000 chars
        "source_date": result[4].isoformat() if result[4] else None,
        "source_url": result[5],
        "validation_status": result[6],
        "created_at": result[7].isoformat() if result[7] else None
    }


@router.get("/{evidence_id}/claims")
async def get_evidence_claims(evidence_id: UUID):
    """Get claims extracted from evidence"""
    query = """
        SELECT id, claim_text, claim_type, polarity, magnitude, confidence
        FROM claims
        WHERE evidence_id = :evidence_id
        ORDER BY created_at DESC
    """
    results = store.fetch_all(query, {"evidence_id": str(evidence_id)})
    
    return [
        {
            "id": row[0],
            "claim_text": row[1],
            "claim_type": row[2],
            "polarity": row[3],
            "magnitude": row[4],
            "confidence": row[5]
        }
        for row in results
    ]
