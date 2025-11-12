"""Financial statements monitoring flow"""
import os
from datetime import datetime
from pathlib import Path
from nexus.storage.postgres import PostgresStore
from nexus.storage.redis_bus import RedisEventBus
from nexus.ingestion.financial_connectors import FinancialDataConnector
from nexus.ingestion.financial_parsers import FinancialStatementsParser
from nexus.ingestion.validators import EvidenceValidator


def monitor_financials():
    """Monitor and process financial statements for tracked companies"""
    print("Starting financial statements monitoring flow...")
    
    store = PostgresStore()
    bus = RedisEventBus()
    connector = FinancialDataConnector()
    parser = FinancialStatementsParser()
    validator = EvidenceValidator()
    
    companies_query = "SELECT id, ticker, name FROM companies WHERE ticker IS NOT NULL AND is_public = true"
    companies = store.fetch_all(companies_query)
    
    if not companies:
        print("No companies found to monitor")
        return
    
    print(f"Monitoring financial statements for {len(companies)} companies...")
    
    for company_row in companies:
        company_id, ticker, name = company_row
        
        print(f"Fetching financials for {ticker} ({name})...")
        
        financial_data = connector.get_financials(ticker)
        
        if "error" in financial_data:
            print(f"Error fetching financials for {ticker}: {financial_data['error']}")
            continue
        
        parsed = parser.parse(financial_data, {})
        
        if "error" in parsed:
            print(f"Error parsing financials for {ticker}: {parsed['error']}")
            continue
        
        period_end = None
        if "income_statement" in parsed.get("metrics", {}):
            period_end = parsed["metrics"]["income_statement"].get("period_end")
        
        evidence_data = {
            "company_id": str(company_id),
            "source_type": "financial_statements",
            "source_url": f"https://finance.yahoo.com/quote/{ticker}/financials",
            "source_date": datetime.strptime(period_end, "%Y-%m-%d").date() if period_end else datetime.utcnow().date(),
            "title": f"{ticker} Financial Statements - {period_end or 'Latest'}",
            "content": parsed["content"],
            "raw_metadata": parsed["metrics"]
        }
        
        is_valid, errors = validator.validate(evidence_data)
        if not is_valid:
            print(f"Validation errors for {ticker}: {errors}")
            continue
        
        evidence_data["validation_status"] = "validated"
        
        evidence_id = store.insert_evidence(evidence_data)
        print(f"Inserted financial statements evidence for {ticker}: {evidence_id}")
        
        event = {
            "evidence_id": str(evidence_id),
            "event_type": "ingestion.raw",
            "timestamp": datetime.utcnow().isoformat(),
            "source": {
                "type": "financial_statements",
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
            "ingested_by": "monitor_financials_flow"
        }
        
        bus.publish("ingestion.raw", event)
        print(f"Published ingestion event for {ticker}")
        
        store.log_provenance({
            "event_type": "data.ingested",
            "entity_type": "evidence",
            "entity_id": evidence_id,
            "action": "financial_statements_fetched",
            "actor": "monitor_financials_flow",
            "payload": {
                "ticker": ticker,
                "period_end": period_end,
                "source": parsed["source"]
            }
        })
    
    print(f"Financial statements monitoring complete. Processed {len(companies)} companies.")


if __name__ == "__main__":
    monitor_financials()
