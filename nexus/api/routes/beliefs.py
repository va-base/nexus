"""Beliefs API routes"""
from uuid import UUID
from fastapi import APIRouter, HTTPException
from nexus.storage.postgres import PostgresStore

router = APIRouter()
store = PostgresStore()


@router.get("/current")
async def get_current_beliefs(limit: int = 100):
    """Get current beliefs for all active hypotheses"""
    query = """
        SELECT h.id, h.statement, cb.current_belief, cb.uncertainty, cb.last_updated
        FROM hypotheses h
        JOIN current_beliefs cb ON h.id = cb.hypothesis_id
        WHERE h.status = 'active'
        ORDER BY cb.last_updated DESC
        LIMIT :limit
    """
    results = store.fetch_all(query, {"limit": limit})
    
    return [
        {
            "hypothesis_id": row[0],
            "statement": row[1],
            "current_belief": row[2],
            "uncertainty": row[3],
            "last_updated": row[4].isoformat() if row[4] else None
        }
        for row in results
    ]


@router.get("/updates/recent")
async def get_recent_updates(limit: int = 50):
    """Get recent belief updates"""
    query = """
        SELECT bu.id, bu.hypothesis_id, h.statement, bu.prior_belief, 
               bu.posterior_belief, bu.log_odds_delta, bu.uncertainty,
               bu.trigger_reason, bu.created_at
        FROM belief_updates bu
        JOIN hypotheses h ON bu.hypothesis_id = h.id
        ORDER BY bu.created_at DESC
        LIMIT :limit
    """
    results = store.fetch_all(query, {"limit": limit})
    
    return [
        {
            "id": row[0],
            "hypothesis_id": row[1],
            "statement": row[2],
            "prior_belief": row[3],
            "posterior_belief": row[4],
            "log_odds_delta": row[5],
            "uncertainty": row[6],
            "trigger_reason": row[7],
            "created_at": row[8].isoformat() if row[8] else None
        }
        for row in results
    ]


@router.get("/updates/{update_id}")
async def get_belief_update_details(update_id: UUID):
    """Get detailed belief update with contributing claims"""
    query = """
        SELECT bu.id, bu.hypothesis_id, h.statement, bu.prior_belief, 
               bu.posterior_belief, bu.log_odds_delta, bu.uncertainty,
               bu.contributing_claims, bu.reliability_score, bu.recency_score,
               bu.relevance_score, bu.trigger_reason, bu.created_at, bu.created_by
        FROM belief_updates bu
        JOIN hypotheses h ON bu.hypothesis_id = h.id
        WHERE bu.id = :id
    """
    result = store.fetch_one(query, {"id": str(update_id)})
    
    if not result:
        raise HTTPException(status_code=404, detail="Belief update not found")
    
    return {
        "id": result[0],
        "hypothesis_id": result[1],
        "statement": result[2],
        "prior_belief": result[3],
        "posterior_belief": result[4],
        "log_odds_delta": result[5],
        "uncertainty": result[6],
        "contributing_claims": result[7],
        "reliability_score": result[8],
        "recency_score": result[9],
        "relevance_score": result[10],
        "trigger_reason": result[11],
        "created_at": result[12].isoformat() if result[12] else None,
        "created_by": result[13]
    }
