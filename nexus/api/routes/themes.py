"""Themes API routes"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from nexus.storage.postgres import PostgresStore

router = APIRouter()
store = PostgresStore()


class ThemeResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    parent_theme_id: Optional[UUID]


class ThemeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_theme_id: Optional[UUID] = None


@router.get("/", response_model=List[ThemeResponse])
async def list_themes(limit: int = 100):
    """List themes"""
    query = """
        SELECT id, name, description, parent_theme_id
        FROM themes
        ORDER BY name
        LIMIT :limit
    """
    results = store.fetch_all(query, {"limit": limit})
    
    return [
        ThemeResponse(
            id=row[0],
            name=row[1],
            description=row[2],
            parent_theme_id=row[3]
        )
        for row in results
    ]


@router.post("/")
async def create_theme(theme: ThemeCreate):
    """Create a new theme"""
    query = """
        INSERT INTO themes (name, description, parent_theme_id)
        VALUES (:name, :description, :parent_theme_id)
        RETURNING id, name, description, parent_theme_id
    """
    result = store.execute(query, {
        "name": theme.name,
        "description": theme.description,
        "parent_theme_id": str(theme.parent_theme_id) if theme.parent_theme_id else None
    })
    row = result.fetchone()
    
    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "parent_theme_id": row[3]
    }


@router.get("/{theme_id}")
async def get_theme(theme_id: UUID):
    """Get theme details"""
    query = """
        SELECT id, name, description, parent_theme_id, metadata, created_at
        FROM themes
        WHERE id = :id
    """
    result = store.fetch_one(query, {"id": str(theme_id)})
    
    if not result:
        raise HTTPException(status_code=404, detail="Theme not found")
    
    return {
        "id": result[0],
        "name": result[1],
        "description": result[2],
        "parent_theme_id": result[3],
        "metadata": result[4],
        "created_at": result[5].isoformat() if result[5] else None
    }


@router.get("/{theme_id}/hypotheses")
async def get_theme_hypotheses(theme_id: UUID, status: str = "active"):
    """Get hypotheses for a theme"""
    query = """
        SELECT h.id, h.statement, h.hypothesis_type, h.status, h.company_id,
               cb.current_belief, cb.uncertainty
        FROM hypotheses h
        LEFT JOIN current_beliefs cb ON h.id = cb.hypothesis_id
        WHERE h.theme_id = :theme_id AND h.status = :status
        ORDER BY h.created_at DESC
    """
    results = store.fetch_all(query, {"theme_id": str(theme_id), "status": status})
    
    return [
        {
            "id": row[0],
            "statement": row[1],
            "hypothesis_type": row[2],
            "status": row[3],
            "company_id": row[4],
            "current_belief": row[5],
            "uncertainty": row[6]
        }
        for row in results
    ]


@router.get("/{theme_id}/companies")
async def get_theme_companies(theme_id: UUID):
    """Get companies associated with a theme"""
    query = """
        SELECT DISTINCT c.id, c.ticker, c.name, c.sector
        FROM companies c
        JOIN hypotheses h ON c.id = h.company_id
        WHERE h.theme_id = :theme_id
        ORDER BY c.name
    """
    results = store.fetch_all(query, {"theme_id": str(theme_id)})
    
    return [
        {
            "id": row[0],
            "ticker": row[1],
            "name": row[2],
            "sector": row[3]
        }
        for row in results
    ]
