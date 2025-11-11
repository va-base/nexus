"""Investigations API routes"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from nexus.storage.postgres import PostgresStore

router = APIRouter()
store = PostgresStore()


class InvestigationResponse(BaseModel):
    id: UUID
    investigation_type: str
    priority: str
    status: str
    trigger_reason: str


@router.get("/", response_model=List[InvestigationResponse])
async def list_investigations(status: str = None, limit: int = 100):
    """List investigations"""
    if status:
        query = """
            SELECT id, investigation_type, priority, status, trigger_reason
            FROM investigations
            WHERE status = :status
            ORDER BY created_at DESC
            LIMIT :limit
        """
        results = store.fetch_all(query, {"status": status, "limit": limit})
    else:
        query = """
            SELECT id, investigation_type, priority, status, trigger_reason
            FROM investigations
            ORDER BY created_at DESC
            LIMIT :limit
        """
        results = store.fetch_all(query, {"limit": limit})
    
    return [
        InvestigationResponse(
            id=row[0],
            investigation_type=row[1],
            priority=row[2],
            status=row[3],
            trigger_reason=row[4] or ""
        )
        for row in results
    ]


@router.get("/{investigation_id}")
async def get_investigation(investigation_id: UUID):
    """Get investigation details"""
    query = """
        SELECT id, hypothesis_id, company_id, investigation_type, trigger_reason,
               priority, status, inputs, outputs, created_at, completed_at
        FROM investigations
        WHERE id = :id
    """
    result = store.fetch_one(query, {"id": str(investigation_id)})
    
    if not result:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    return {
        "id": result[0],
        "hypothesis_id": result[1],
        "company_id": result[2],
        "investigation_type": result[3],
        "trigger_reason": result[4],
        "priority": result[5],
        "status": result[6],
        "inputs": result[7],
        "outputs": result[8],
        "created_at": result[9].isoformat() if result[9] else None,
        "completed_at": result[10].isoformat() if result[10] else None
    }
