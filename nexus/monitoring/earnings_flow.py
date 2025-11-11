"""Earnings transcript monitoring flow"""
import os
from datetime import datetime
from pathlib import Path
from nexus.storage.postgres import PostgresStore
from nexus.storage.redis_bus import RedisEventBus
from nexus.ingestion.parsers import TranscriptParser
from nexus.ingestion.validators import EvidenceValidator


def monitor_earnings():
    """Monitor and process earnings transcripts"""
    print("Starting earnings monitoring flow...")
    
    store = PostgresStore()
    bus = RedisEventBus()
    parser = TranscriptParser()
    validator = EvidenceValidator()
    
    fixtures_dir = Path(os.getenv("FIXTURES_DIR", "/app/data/fixtures"))
    transcript_path = fixtures_dir / "sample_transcript.txt"
    
    if not transcript_path.exists():
        print(f"No transcript fixture found at {transcript_path}")
        return
    
    with open(transcript_path, 'r') as f:
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
        "source_type": "transcript",
        "source_url": "https://earnings.com/sample",
        "source_date": datetime.utcnow().date(),
        "title": "Q3 2025 Earnings Call",
        "content": content
    }
    
    is_valid, errors = validator.validate(evidence_data)
    if not is_valid:
        print(f"Validation errors: {errors}")
        return
    
    evidence_data["validation_status"] = "validated"
    
    evidence_id = store.insert_evidence(evidence_data)
    print(f"Inserted evidence: {evidence_id}")
    
    parsed = parser.parse(content, {})
    
    event = {
        "evidence_id": str(evidence_id),
        "event_type": "ingestion.raw",
        "timestamp": datetime.utcnow().isoformat(),
        "source": {
            "type": "transcript",
            "provider": "earnings_call",
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
            "text": content[:5000],
            "metadata": parsed
        },
        "content_hash": evidence_data.get("content_hash", ""),
        "ingested_by": "monitor_earnings_flow"
    }
    
    bus.publish("ingestion.raw", event)
    print("Published ingestion event")


if __name__ == "__main__":
    monitor_earnings()
