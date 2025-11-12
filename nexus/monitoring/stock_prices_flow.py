"""Stock prices monitoring flow"""
import os
from datetime import datetime, timedelta
from pathlib import Path
from nexus.storage.postgres import PostgresStore
from nexus.storage.redis_bus import RedisEventBus
from nexus.ingestion.financial_connectors import FinancialDataConnector
from nexus.ingestion.financial_parsers import StockPriceParser
from nexus.ingestion.validators import EvidenceValidator


def monitor_stock_prices():
    """Monitor and process stock prices for tracked companies"""
    print("Starting stock prices monitoring flow...")
    
    store = PostgresStore()
    bus = RedisEventBus()
    connector = FinancialDataConnector()
    parser = StockPriceParser()
    validator = EvidenceValidator()
    
    companies_query = "SELECT id, ticker, name FROM companies WHERE ticker IS NOT NULL AND is_public = true"
    companies = store.fetch_all(companies_query)
    
    if not companies:
        print("No companies found to monitor")
        return
    
    print(f"Monitoring stock prices for {len(companies)} companies...")
    
    for company_row in companies:
        company_id, ticker, name = company_row
        
        print(f"Fetching stock price for {ticker} ({name})...")
        
        price_data = connector.get_stock_price(ticker)
        
        if "error" in price_data:
            print(f"Error fetching price for {ticker}: {price_data['error']}")
            continue
        
        parsed = parser.parse(price_data, {})
        
        if "error" in parsed:
            print(f"Error parsing price for {ticker}: {parsed['error']}")
            continue
        
        evidence_data = {
            "company_id": str(company_id),
            "source_type": "stock_price",
            "source_url": f"https://finance.yahoo.com/quote/{ticker}",
            "source_date": datetime.strptime(price_data["date"], "%Y-%m-%d").date(),
            "title": f"{ticker} Stock Price - {price_data['date']}",
            "content": parsed["content"],
            "raw_metadata": parsed["metrics"]
        }
        
        is_valid, errors = validator.validate(evidence_data)
        if not is_valid:
            print(f"Validation errors for {ticker}: {errors}")
            continue
        
        evidence_data["validation_status"] = "validated"
        
        evidence_id = store.insert_evidence(evidence_data)
        print(f"Inserted stock price evidence for {ticker}: {evidence_id}")
        
        event = {
            "evidence_id": str(evidence_id),
            "event_type": "ingestion.raw",
            "timestamp": datetime.utcnow().isoformat(),
            "source": {
                "type": "stock_price",
                "provider": parsed["source"],
                "url": evidence_data["source_url"],
                "date": str(evidence_data["source_date"])
            },
            "company": {
                "id": str(company_id),
                "ticker": ticker,
                "name": name
            },
            "content": {
                "title": evidence_data["title"],
                "text": parsed["content"],
                "metadata": parsed["metrics"]
            },
            "content_hash": evidence_data.get("content_hash", ""),
            "ingested_by": "monitor_stock_prices_flow"
        }
        
        bus.publish("ingestion.raw", event)
        print(f"Published ingestion event for {ticker}")
        
        store.log_provenance({
            "event_type": "data.ingested",
            "entity_type": "evidence",
            "entity_id": evidence_id,
            "action": "stock_price_fetched",
            "actor": "monitor_stock_prices_flow",
            "payload": {
                "ticker": ticker,
                "date": price_data["date"],
                "source": parsed["source"]
            }
        })
    
    print(f"Stock prices monitoring complete. Processed {len(companies)} companies.")


def monitor_historical_prices(ticker: str, days: int = 30):
    """
    Monitor historical stock prices for a specific company
    
    Args:
        ticker: Stock ticker symbol
        days: Number of days of historical data to fetch
    """
    print(f"Fetching {days} days of historical prices for {ticker}...")
    
    store = PostgresStore()
    bus = RedisEventBus()
    connector = FinancialDataConnector()
    parser = StockPriceParser()
    validator = EvidenceValidator()
    
    company_query = "SELECT id, name FROM companies WHERE ticker = :ticker LIMIT 1"
    result = store.fetch_one(company_query, {"ticker": ticker})
    
    if not result:
        print(f"Company not found for ticker {ticker}")
        return
    
    company_id, name = result
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    prices = connector.get_historical_prices(
        ticker,
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )
    
    if not prices or "error" in prices[0]:
        print(f"Error fetching historical prices for {ticker}")
        return
    
    parsed = parser.parse_historical(prices, {})
    
    if "error" in parsed:
        print(f"Error parsing historical prices for {ticker}: {parsed['error']}")
        return
    
    evidence_data = {
        "company_id": str(company_id),
        "source_type": "historical_prices",
        "source_url": f"https://finance.yahoo.com/quote/{ticker}/history",
        "source_date": end_date.date(),
        "title": f"{ticker} Historical Prices - {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        "content": parsed["content"],
        "raw_metadata": parsed["metrics"]
    }
    
    is_valid, errors = validator.validate(evidence_data)
    if not is_valid:
        print(f"Validation errors: {errors}")
        return
    
    evidence_data["validation_status"] = "validated"
    evidence_id = store.insert_evidence(evidence_data)
    print(f"Inserted historical prices evidence: {evidence_id}")
    
    event = {
        "evidence_id": str(evidence_id),
        "event_type": "ingestion.raw",
        "timestamp": datetime.utcnow().isoformat(),
        "source": {
            "type": "historical_prices",
            "provider": parsed["source"],
            "url": evidence_data["source_url"],
            "date": str(evidence_data["source_date"])
        },
        "company": {
            "id": str(company_id),
            "ticker": ticker,
            "name": name
        },
        "content": {
            "title": evidence_data["title"],
            "text": parsed["content"],
            "metadata": parsed["metrics"]
        },
        "content_hash": evidence_data.get("content_hash", ""),
        "ingested_by": "monitor_historical_prices_flow"
    }
    
    bus.publish("ingestion.raw", event)
    print(f"Published historical prices event for {ticker}")


if __name__ == "__main__":
    monitor_stock_prices()
