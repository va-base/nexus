"""Run smoke test to verify system is working"""
import os
import sys
import time
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from nexus.storage.postgres import PostgresStore
from nexus.storage.redis_bus import RedisEventBus
from nexus.extraction.mock_extractor import MockExtractor
from nexus.belief.engine import BeliefEngine
from nexus.utils.embeddings import EmbeddingGenerator


def run_smoke_test():
    """Run smoke test"""
    print("Running smoke test...")
    
    print("\n1. Testing database connection...")
    try:
        store = PostgresStore()
        result = store.fetch_one("SELECT 1")
        assert result[0] == 1
        print("✓ Database connection OK")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False
    
    print("\n2. Testing Redis connection...")
    try:
        bus = RedisEventBus()
        bus.client.ping()
        print("✓ Redis connection OK")
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        return False
    
    print("\n3. Testing mock extractor...")
    try:
        extractor = MockExtractor()
        claims = extractor.extract_claims("Revenue of $150 million grew 35% YoY")
        assert len(claims) > 0
        print(f"✓ Mock extractor OK (extracted {len(claims)} claims)")
    except Exception as e:
        print(f"✗ Mock extractor failed: {e}")
        return False
    
    print("\n4. Checking fixtures...")
    try:
        result = store.fetch_one("SELECT COUNT(*) FROM companies")
        company_count = result[0]
        
        result = store.fetch_one("SELECT COUNT(*) FROM hypotheses")
        hypothesis_count = result[0]
        
        print(f"✓ Fixtures OK (companies: {company_count}, hypotheses: {hypothesis_count})")
    except Exception as e:
        print(f"✗ Fixtures check failed: {e}")
        return False
    
    print("\n5. Testing belief engine...")
    try:
        engine = BeliefEngine(store)
        print("✓ Belief engine OK")
    except Exception as e:
        print(f"✗ Belief engine failed: {e}")
        return False
    
    print("\n6. Testing end-to-end belief update flow...")
    try:
        embedding_gen = EmbeddingGenerator()
        
        query = "SELECT id FROM companies LIMIT 1"
        result = store.fetch_one(query)
        if not result:
            print("✗ No companies found in database")
            return False
        company_id = result[0]
        
        hypothesis_statement = "Test hypothesis: Revenue will grow 30% YoY"
        hypothesis_embedding = embedding_gen.encode(hypothesis_statement)
        
        hypothesis_id = store.insert_hypothesis({
            "company_id": str(company_id),
            "statement": hypothesis_statement,
            "hypothesis_type": "growth",
            "initial_belief": 0.5,
            "embedding": hypothesis_embedding,
            "created_by": "smoke_test"
        })
        print(f"  - Created test hypothesis: {hypothesis_id}")
        
        evidence_id = store.insert_evidence({
            "company_id": str(company_id),
            "source_type": "manual",
            "title": "Test Evidence",
            "content": "Revenue grew 35% year-over-year to $150 million",
            "ingested_by": "smoke_test"
        })
        print(f"  - Created test evidence: {evidence_id}")
        
        claims = extractor.extract_claims("Revenue grew 35% year-over-year to $150 million")
        claim_ids = []
        for claim in claims:
            claim_embedding = embedding_gen.encode(claim["claim_text"])
            claim_id = store.insert_claim({
                "evidence_id": str(evidence_id),
                "company_id": str(company_id),
                "claim_text": claim["claim_text"],
                "claim_type": claim.get("claim_type"),
                "polarity": claim.get("polarity"),
                "magnitude": claim.get("magnitude"),
                "confidence": claim.get("confidence"),
                "embedding": claim_embedding,
                "model_version": "mock"
            })
            claim_ids.append(claim_id)
        print(f"  - Created {len(claim_ids)} test claims")
        
        update = engine.update_belief(hypothesis_id, claim_ids, trigger_reason="smoke_test")
        print(f"  - Belief updated: {update['prior_belief']:.3f} -> {update['posterior_belief']:.3f}")
        
        query = "SELECT posterior_belief FROM belief_updates WHERE hypothesis_id = :id ORDER BY created_at DESC LIMIT 1"
        result = store.fetch_one(query, {"id": str(hypothesis_id)})
        if result:
            print(f"✓ End-to-end belief update flow OK (final belief: {result[0]:.3f})")
        else:
            print("✗ Belief update not found in database")
            return False
            
    except Exception as e:
        print(f"✗ End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✓ All smoke tests passed!")
    return True


if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
