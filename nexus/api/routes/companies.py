"""Companies API routes"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from nexus.storage.postgres import PostgresStore

router = APIRouter()
store = PostgresStore()


class CompanyResponse(BaseModel):
    id: UUID
    ticker: Optional[str]
    name: str
    sector: Optional[str]
    market_cap: Optional[int]
    is_public: bool


class CompanyCreate(BaseModel):
    ticker: Optional[str] = None
    name: str
    sector: Optional[str] = None
    market_cap: Optional[int] = None
    is_public: bool = True


@router.get("/", response_model=List[CompanyResponse])
async def list_companies(limit: int = 100, sector: Optional[str] = None):
    """List companies"""
    if sector:
        query = """
            SELECT id, ticker, name, sector, market_cap, is_public
            FROM companies
            WHERE sector = :sector
            ORDER BY name
            LIMIT :limit
        """
        results = store.fetch_all(query, {"sector": sector, "limit": limit})
    else:
        query = """
            SELECT id, ticker, name, sector, market_cap, is_public
            FROM companies
            ORDER BY name
            LIMIT :limit
        """
        results = store.fetch_all(query, {"limit": limit})
    
    return [
        CompanyResponse(
            id=row[0],
            ticker=row[1],
            name=row[2],
            sector=row[3],
            market_cap=row[4],
            is_public=row[5]
        )
        for row in results
    ]


@router.post("/", response_model=CompanyResponse)
async def create_company(company: CompanyCreate):
    """Create a new company"""
    company_data = {
        "ticker": company.ticker,
        "name": company.name,
        "sector": company.sector,
        "market_cap": company.market_cap,
        "is_public": company.is_public
    }
    
    company_id = store.insert_company(company_data)
    
    return CompanyResponse(
        id=company_id,
        ticker=company.ticker,
        name=company.name,
        sector=company.sector,
        market_cap=company.market_cap,
        is_public=company.is_public
    )


@router.get("/{company_id}")
async def get_company(company_id: UUID):
    """Get company details"""
    query = """
        SELECT id, ticker, name, sector, market_cap, is_public, metadata, created_at
        FROM companies
        WHERE id = :id
    """
    result = store.fetch_one(query, {"id": str(company_id)})
    
    if not result:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return {
        "id": result[0],
        "ticker": result[1],
        "name": result[2],
        "sector": result[3],
        "market_cap": result[4],
        "is_public": result[5],
        "metadata": result[6],
        "created_at": result[7].isoformat() if result[7] else None
    }


@router.get("/{company_id}/hypotheses")
async def get_company_hypotheses(company_id: UUID, status: str = "active"):
    """Get hypotheses for a company"""
    query = """
        SELECT h.id, h.statement, h.hypothesis_type, h.status, cb.current_belief, cb.uncertainty
        FROM hypotheses h
        LEFT JOIN current_beliefs cb ON h.id = cb.hypothesis_id
        WHERE h.company_id = :company_id AND h.status = :status
        ORDER BY h.created_at DESC
    """
    results = store.fetch_all(query, {"company_id": str(company_id), "status": status})
    
    return [
        {
            "id": row[0],
            "statement": row[1],
            "hypothesis_type": row[2],
            "status": row[3],
            "current_belief": row[4],
            "uncertainty": row[5]
        }
        for row in results
    ]


@router.get("/{company_id}/evidence")
async def get_company_evidence(company_id: UUID, limit: int = 50):
    """Get evidence for a company"""
    query = """
        SELECT id, source_type, title, source_date, validation_status, created_at
        FROM evidence
        WHERE company_id = :company_id
        ORDER BY source_date DESC, created_at DESC
        LIMIT :limit
    """
    results = store.fetch_all(query, {"company_id": str(company_id), "limit": limit})
    
    return [
        {
            "id": row[0],
            "source_type": row[1],
            "title": row[2],
            "source_date": row[3].isoformat() if row[3] else None,
            "validation_status": row[4],
            "created_at": row[5].isoformat() if row[5] else None
        }
        for row in results
    ]


@router.get("/{company_id}/investigations")
async def get_company_investigations(company_id: UUID, limit: int = 50):
    """Get investigations for a company"""
    query = """
        SELECT id, investigation_type, priority, status, trigger_reason, created_at
        FROM investigations
        WHERE company_id = :company_id
        ORDER BY created_at DESC
        LIMIT :limit
    """
    results = store.fetch_all(query, {"company_id": str(company_id), "limit": limit})
    
    return [
        {
            "id": row[0],
            "investigation_type": row[1],
            "priority": row[2],
            "status": row[3],
            "trigger_reason": row[4],
            "created_at": row[5].isoformat() if row[5] else None
        }
        for row in results
    ]
