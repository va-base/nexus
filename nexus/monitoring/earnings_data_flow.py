"""Earnings data monitoring flow"""
import os
from datetime import datetime
from pathlib import Path
from nexus.storage.postgres import PostgresStore
from nexus.storage.redis_bus import RedisEventBus
from nexus.ingestion.financial_connectors import FinancialDataConnector
from nexus.ingestion.financial_parsers import EarningsParser
from nexus.ingestion.validators import EvidenceValidator


def monitor_earnings_data():
    """Monitor and process earnings data for tracked companies"""
    print("Starting earnings data monitoring flow...")
    
    store = PostgresStore()
    bus = RedisEventBus()
    connector = FinancialDataConnector()
    parser = EarningsParser()
    validator = EvidenceValidator()
    
    companies_query = "SELECT id, ticker, name FROM companies WHERE ticker IS NOT NULL AND is_public = true"
    companies = store.fetch_all(companies_query)
    
    if not companies:
        print("No companies found to monitor")
        return
    
    print(f"Monitoring earnings data for {len(companies)} companies...")
    
    for company_row in companies:
        company_id, ticker, name = company_row
        
        print(f"Fetching earnings for {ticker} ({name})...")
        
        earnings_data = connector.get_earnings(ticker)
        
        if "error" in earnings_data:
            print(f"Error fetching earnings for {ticker}: {earnings_data['error']}")
            continue
        
        parsed = parser.parse(earnings_data, {})
        
        if "error" in parsed:
            print(f"Error parsing earnings for {ticker}: {parsed['error']}")
            continue
        
        earnings_date = None
        if "quarterly_earnings" in parsed.get("metrics", {}):
            quarterly = parsed["metrics"]["quarterly_earnings"]
            if quarterly:
                earnings_date = quarterly[0].get("date")
        
        evidence_data = {
            "company_id": str(company_id),
            "source_type": "earnings",
            "source_url": f"https://finance.yahoo.com/quote/{ticker}/analysis",
            "source_date": datetime.strptime(earnings_date, "%Y-%m-%d").date() if earnings_date else datetime.utcnow().date(),
            "title": f"{ticker} Earnings Data - {earnings_date or 'Latest'}",
            "content": parsed["content"],
            "raw_metadata": parsed["metrics"]
        }
        
        is_valid, errors = validator.validate(evidence_data)
        if not is_valid:
            print(f"Validation errors for {ticker}: {errors}")
            continue
        
        evidence_data["validation_status"] = "validated"
        
        evidence_id = store.insert_evidence(evidence_data)
        print(f"Inserted earnings evidence for {ticker}: {evidence_id}")
        
        event = {
            "evidence_id": str(evidence_id),
            "event_type": "ingestion.raw",
            "timestamp": datetime.utcnow().isoformat(),
            "source": {
                "type": "earnings",
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
            "ingested_by": "monitor_earnings_data_flow"
        }
        
        bus.publish("ingestion.raw", event)
        print(f"Published ingestion event for {ticker}")
        
        store.log_provenance({
            "event_type": "data.ingested",
            "entity_type": "evidence",
            "entity_id": evidence_id,
            "action": "earnings_data_fetched",
            "actor": "monitor_earnings_data_flow",
            "payload": {
                "ticker": ticker,
                "earnings_date": earnings_date,
                "source": parsed["source"]
            }
        })
    
    print(f"Earnings data monitoring complete. Processed {len(companies)} companies.")


if __name__ == "__main__":
    monitor_earnings_data()
