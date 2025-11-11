"""Run smoke test to verify system is working"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from nexus.storage.postgres import PostgresStore
from nexus.storage.redis_bus import RedisEventBus
from nexus.extraction.mock_extractor import MockExtractor
from nexus.belief.engine import BeliefEngine


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
    
    print("\n✓ All smoke tests passed!")
    return True


if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
