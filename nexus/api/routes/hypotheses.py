"""Hypotheses API routes"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from nexus.storage.postgres import PostgresStore
from nexus.utils.embeddings import EmbeddingGenerator

router = APIRouter()
store = PostgresStore()
embedding_gen = EmbeddingGenerator()


class HypothesisCreate(BaseModel):
    company_id: Optional[UUID] = None
    theme_id: Optional[UUID] = None
    statement: str
    hypothesis_type: Optional[str] = None
    time_horizon: Optional[str] = None
    initial_belief: float = 0.5


class HypothesisResponse(BaseModel):
    id: UUID
    statement: str
    hypothesis_type: Optional[str]
    current_belief: Optional[float]
    status: str


@router.get("/", response_model=List[HypothesisResponse])
async def list_hypotheses(status: str = "active", limit: int = 100):
    """List hypotheses"""
    query = """
        SELECT h.id, h.statement, h.hypothesis_type, h.status, cb.current_belief
        FROM hypotheses h
        LEFT JOIN current_beliefs cb ON h.id = cb.hypothesis_id
        WHERE h.status = :status
        ORDER BY h.created_at DESC
        LIMIT :limit
    """
    results = store.fetch_all(query, {"status": status, "limit": limit})
    
    return [
        HypothesisResponse(
            id=row[0],
            statement=row[1],
            hypothesis_type=row[2],
            status=row[3],
            current_belief=row[4]
        )
        for row in results
    ]


@router.post("/", response_model=HypothesisResponse)
async def create_hypothesis(hypothesis: HypothesisCreate):
    """Create a new hypothesis"""
    embedding = embedding_gen.encode(hypothesis.statement)
    
    hypothesis_data = {
        "company_id": str(hypothesis.company_id) if hypothesis.company_id else None,
        "theme_id": str(hypothesis.theme_id) if hypothesis.theme_id else None,
        "statement": hypothesis.statement,
        "hypothesis_type": hypothesis.hypothesis_type,
        "time_horizon": hypothesis.time_horizon,
        "initial_belief": hypothesis.initial_belief,
        "embedding": embedding,
        "created_by": "api"
    }
    
    hypothesis_id = store.insert_hypothesis(hypothesis_data)
    
    return HypothesisResponse(
        id=hypothesis_id,
        statement=hypothesis.statement,
        hypothesis_type=hypothesis.hypothesis_type,
        current_belief=hypothesis.initial_belief,
        status="active"
    )


@router.get("/{hypothesis_id}")
async def get_hypothesis(hypothesis_id: UUID):
    """Get hypothesis details"""
    query = """
        SELECT h.id, h.statement, h.hypothesis_type, h.status, h.created_at,
               cb.current_belief, cb.uncertainty, cb.last_updated
        FROM hypotheses h
        LEFT JOIN current_beliefs cb ON h.id = cb.hypothesis_id
        WHERE h.id = :id
    """
    result = store.fetch_one(query, {"id": str(hypothesis_id)})
    
    if not result:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    
    return {
        "id": result[0],
        "statement": result[1],
        "hypothesis_type": result[2],
        "status": result[3],
        "created_at": result[4].isoformat() if result[4] else None,
        "current_belief": result[5],
        "uncertainty": result[6],
        "last_updated": result[7].isoformat() if result[7] else None
    }


@router.get("/{hypothesis_id}/history")
async def get_belief_history(hypothesis_id: UUID, limit: int = 50):
    """Get belief update history for a hypothesis"""
    query = """
        SELECT id, prior_belief, posterior_belief, log_odds_delta, 
               uncertainty, trigger_reason, created_at
        FROM belief_updates
        WHERE hypothesis_id = :hypothesis_id
        ORDER BY created_at DESC
        LIMIT :limit
    """
    results = store.fetch_all(query, {"hypothesis_id": str(hypothesis_id), "limit": limit})
    
    return [
        {
            "id": row[0],
            "prior_belief": row[1],
            "posterior_belief": row[2],
            "log_odds_delta": row[3],
            "uncertainty": row[4],
            "trigger_reason": row[5],
            "created_at": row[6].isoformat() if row[6] else None
        }
        for row in results
    ]
