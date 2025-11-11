"""Hiring data monitoring flow"""
import os
import json
from datetime import datetime
from pathlib import Path
from nexus.storage.postgres import PostgresStore
from nexus.storage.redis_bus import RedisEventBus
from nexus.ingestion.parsers import JobPostingParser
from nexus.ingestion.validators import EvidenceValidator


def monitor_hiring():
    """Monitor and process hiring data"""
    print("Starting hiring monitoring flow...")
    
    store = PostgresStore()
    bus = RedisEventBus()
    parser = JobPostingParser()
    validator = EvidenceValidator()
    
    fixtures_dir = Path(os.getenv("FIXTURES_DIR", "/app/data/fixtures"))
    hiring_path = fixtures_dir / "sample_hiring.json"
    
    if not hiring_path.exists():
        print(f"No hiring fixture found at {hiring_path}")
        return
    
    with open(hiring_path, 'r') as f:
        hiring_data = json.load(f)
    
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
    
    for posting in hiring_data.get("postings", []):
        content = posting.get("description", "")
        
        evidence_data = {
            "company_id": str(company_id),
            "source_type": "hiring",
            "source_url": posting.get("url", ""),
            "source_date": datetime.utcnow().date(),
            "title": posting.get("title", ""),
            "content": content
        }
        
        is_valid, errors = validator.validate(evidence_data)
        if not is_valid:
            print(f"Validation errors for {posting.get('title')}: {errors}")
            continue
        
        evidence_data["validation_status"] = "validated"
        
        evidence_id = store.insert_evidence(evidence_data)
        print(f"Inserted hiring evidence: {evidence_id}")
        
        parsed = parser.parse(content, posting)
        
        event = {
            "evidence_id": str(evidence_id),
            "event_type": "ingestion.raw",
            "timestamp": datetime.utcnow().isoformat(),
            "source": {
                "type": "hiring",
                "provider": "greenhouse",
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
                "text": content,
                "metadata": parsed
            },
            "content_hash": evidence_data.get("content_hash", ""),
            "ingested_by": "monitor_hiring_flow"
        }
        
        bus.publish("ingestion.raw", event)
    
    print(f"Published {len(hiring_data.get('postings', []))} hiring events")


if __name__ == "__main__":
    monitor_hiring()
