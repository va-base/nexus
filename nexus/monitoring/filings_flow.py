"""SEC filings monitoring flow"""
import os
from datetime import datetime
from pathlib import Path
from nexus.storage.postgres import PostgresStore
from nexus.storage.redis_bus import RedisEventBus
from nexus.ingestion.parsers import FilingParser
from nexus.ingestion.validators import EvidenceValidator
from nexus.ingestion.mnpi_filter import MNPIFilter


def monitor_filings():
    """Monitor and process SEC filings"""
    print("Starting filings monitoring flow...")
    
    store = PostgresStore()
    bus = RedisEventBus()
    parser = FilingParser()
    validator = EvidenceValidator()
    mnpi_filter = MNPIFilter()
    
    fixtures_dir = Path(os.getenv("FIXTURES_DIR", "/app/data/fixtures"))
    filing_path = fixtures_dir / "sample_10q.html"
    
    if not filing_path.exists():
        print(f"No filing fixture found at {filing_path}")
        return
    
    with open(filing_path, 'r') as f:
        content = f.read()
    
    company_query = "SELECT id FROM companies WHERE ticker = 'ACME' LIMIT 1"
    result = store.fetch_one(company_query)
    
    if result:
        company_id = result[0]
    else:
        company_id = store.insert_company({
            "ticker": "ACME",
            "name": "Acme Corp",
            "sector": "Technology",
            "is_public": True
        })
    
    evidence_data = {
        "company_id": str(company_id),
        "source_type": "filing",
        "source_url": "https://sec.gov/sample",
        "source_date": datetime.utcnow().date(),
        "title": "Q3 2025 10-Q Filing",
        "content": content
    }
    
    is_valid, errors = validator.validate(evidence_data)
    if not is_valid:
        print(f"Validation errors: {errors}")
        return
    
    has_mnpi, mnpi_flags = mnpi_filter.check(content, evidence_data)
    if has_mnpi:
        print(f"MNPI detected: {mnpi_flags}")
        evidence_data["validation_status"] = "mnpi_hold"
    else:
        evidence_data["validation_status"] = "validated"
    
    evidence_id = store.insert_evidence(evidence_data)
    print(f"Inserted evidence: {evidence_id}")
    
    parsed = parser.parse(content, {"filing_type": "10-Q"})
    
    event = {
        "evidence_id": str(evidence_id),
        "event_type": "ingestion.raw",
        "timestamp": datetime.utcnow().isoformat(),
        "source": {
            "type": "filing",
            "provider": "sec",
            "url": evidence_data["source_url"],
            "date": str(evidence_data["source_date"])
        },
        "company": {
            "id": str(company_id),
            "ticker": "ACME",
            "name": "Acme Corp"
        },
        "content": {
            "title": evidence_data["title"],
            "text": content[:5000],  # First 5000 chars
            "metadata": parsed
        },
        "content_hash": evidence_data.get("content_hash", ""),
        "ingested_by": "monitor_filings_flow"
    }
    
    bus.publish("ingestion.raw", event)
    print("Published ingestion event")


if __name__ == "__main__":
    monitor_filings()
