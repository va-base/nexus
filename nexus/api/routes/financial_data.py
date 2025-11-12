"""Financial data API routes"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from nexus.storage.postgres import PostgresStore
from nexus.ingestion.financial_connectors import FinancialDataConnector


router = APIRouter()


class StockPriceResponse(BaseModel):
    """Stock price response model"""
    ticker: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str


class FinancialStatementsResponse(BaseModel):
    """Financial statements response model"""
    ticker: str
    income_statement: Optional[dict] = None
    balance_sheet: Optional[dict] = None
    cash_flow: Optional[dict] = None
    source: str


class EarningsResponse(BaseModel):
    """Earnings response model"""
    ticker: str
    quarterly_earnings: Optional[List[dict]] = None
    annual_earnings: Optional[List[dict]] = None
    metrics: Optional[dict] = None
    source: str


class CompanyInfoResponse(BaseModel):
    """Company info response model"""
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[int] = None
    description: Optional[str] = None


@router.get("/stock-price/{ticker}", response_model=StockPriceResponse)
async def get_stock_price(ticker: str):
    """
    Get current stock price for a ticker
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
    
    Returns:
        Current stock price data
    """
    try:
        connector = FinancialDataConnector()
        price_data = connector.get_stock_price(ticker.upper())
        
        if "error" in price_data:
            raise HTTPException(status_code=404, detail=price_data["error"])
        
        return price_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/historical-prices/{ticker}", response_model=List[StockPriceResponse])
async def get_historical_prices(
    ticker: str,
    days: int = Query(default=30, ge=1, le=365, description="Number of days of historical data")
):
    """
    Get historical stock prices for a ticker
    
    Args:
        ticker: Stock ticker symbol
        days: Number of days of historical data (1-365)
    
    Returns:
        List of historical price data
    """
    try:
        connector = FinancialDataConnector()
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        prices = connector.get_historical_prices(
            ticker.upper(),
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )
        
        if not prices or "error" in prices[0]:
            raise HTTPException(status_code=404, detail="No historical data found")
        
        return prices
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/financials/{ticker}", response_model=FinancialStatementsResponse)
async def get_financials(ticker: str):
    """
    Get financial statements for a ticker
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Financial statements (income statement, balance sheet, cash flow)
    """
    try:
        connector = FinancialDataConnector()
        financial_data = connector.get_financials(ticker.upper())
        
        if "error" in financial_data:
            raise HTTPException(status_code=404, detail=financial_data["error"])
        
        return financial_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/earnings/{ticker}", response_model=EarningsResponse)
async def get_earnings(ticker: str):
    """
    Get earnings data for a ticker
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Earnings data (quarterly, annual, metrics)
    """
    try:
        connector = FinancialDataConnector()
        earnings_data = connector.get_earnings(ticker.upper())
        
        if "error" in earnings_data:
            raise HTTPException(status_code=404, detail=earnings_data["error"])
        
        return earnings_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company-info/{ticker}", response_model=CompanyInfoResponse)
async def get_company_info(ticker: str):
    """
    Get company information for a ticker
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Company information
    """
    try:
        connector = FinancialDataConnector()
        company_data = connector.get_company_info(ticker.upper())
        
        if "error" in company_data:
            raise HTTPException(status_code=404, detail=company_data["error"])
        
        return company_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evidence/financial/{ticker}")
async def get_financial_evidence(
    ticker: str,
    limit: int = Query(default=10, ge=1, le=100, description="Number of records to return")
):
    """
    Get financial evidence records for a ticker from the database
    
    Args:
        ticker: Stock ticker symbol
        limit: Number of records to return (1-100)
    
    Returns:
        List of financial evidence records
    """
    try:
        store = PostgresStore()
        
        company_query = "SELECT id FROM companies WHERE ticker = :ticker LIMIT 1"
        result = store.fetch_one(company_query, {"ticker": ticker.upper()})
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Company not found for ticker {ticker}")
        
        company_id = result[0]
        
        evidence_query = """
            SELECT id, source_type, source_date, title, raw_metadata, created_at
            FROM evidence
            WHERE company_id = :company_id
            AND source_type IN ('stock_price', 'financial_statements', 'earnings', 'historical_prices')
            ORDER BY source_date DESC, created_at DESC
            LIMIT :limit
        """
        
        results = store.fetch_all(evidence_query, {
            "company_id": str(company_id),
            "limit": limit
        })
        
        evidence_list = []
        for row in results:
            evidence_list.append({
                "id": str(row[0]),
                "source_type": row[1],
                "source_date": str(row[2]) if row[2] else None,
                "title": row[3],
                "metadata": row[4],
                "created_at": row[5].isoformat() if row[5] else None
            })
        
        return {
            "ticker": ticker.upper(),
            "company_id": str(company_id),
            "count": len(evidence_list),
            "evidence": evidence_list
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
