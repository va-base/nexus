"""Seed database with fixture data"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from nexus.storage.postgres import PostgresStore
from nexus.utils.embeddings import EmbeddingGenerator

def seed_fixtures():
    """Seed database with fixture data"""
    print("Seeding fixtures...")
    
    store = PostgresStore()
    embedding_gen = EmbeddingGenerator()
    
    print("Creating sample company...")
    company_id = store.insert_company({
        "ticker": "ACME",
        "name": "Acme Corp",
        "sector": "Technology",
        "market_cap": 50000000000,
        "is_public": True,
        "metadata": {"founded": 2010}
    })
    print(f"Created company: {company_id}")
    
    print("Creating sample theme...")
    query = """
        INSERT INTO themes (name, description)
        VALUES (:name, :description)
        RETURNING id
    """
    result = store.execute(query, {
        "name": "AI Infrastructure",
        "description": "Companies building AI infrastructure and tools"
    })
    theme_id = result.fetchone()[0]
    print(f"Created theme: {theme_id}")
    
    print("Creating sample hypotheses...")
    hypotheses = [
        {
            "company_id": str(company_id),
            "theme_id": str(theme_id),
            "statement": "ACME revenue growth will exceed 30% YoY in Q4 2025",
            "hypothesis_type": "growth",
            "time_horizon": "short_term",
            "initial_belief": 0.6
        },
        {
            "company_id": str(company_id),
            "theme_id": str(theme_id),
            "statement": "ACME is scaling its AI engineering team aggressively",
            "hypothesis_type": "operational",
            "time_horizon": "medium_term",
            "initial_belief": 0.5
        },
        {
            "company_id": str(company_id),
            "theme_id": str(theme_id),
            "statement": "ACME gross margins will expand by 200bps in 2026",
            "hypothesis_type": "margin",
            "time_horizon": "medium_term",
            "initial_belief": 0.55
        }
    ]
    
    for hyp in hypotheses:
        embedding = embedding_gen.encode(hyp["statement"])
        hyp["embedding"] = embedding
        hyp["created_by"] = "seed_script"
        
        hypothesis_id = store.insert_hypothesis(hyp)
        print(f"Created hypothesis: {hypothesis_id}")
    
    print("Creating sample predictions...")
    from datetime import date, timedelta
    
    query = """
        INSERT INTO predictions (company_id, metric_name, predicted_value, 
                                confidence_lower, confidence_upper, 
                                prediction_date, target_date)
        VALUES (:company_id, :metric_name, :predicted_value,
                :confidence_lower, :confidence_upper,
                :prediction_date, :target_date)
    """
    
    target_date = date.today() + timedelta(days=90)
    
    store.execute(query, {
        "company_id": str(company_id),
        "metric_name": "revenue",
        "predicted_value": 150.0,
        "confidence_lower": 140.0,
        "confidence_upper": 160.0,
        "prediction_date": date.today(),
        "target_date": target_date
    })
    
    print("Fixtures seeded successfully!")


if __name__ == "__main__":
    seed_fixtures()
