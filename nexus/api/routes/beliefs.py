"""Beliefs API routes"""
from fastapi import APIRouter
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
