"""Vector store adapter using pgvector"""
from typing import List, Tuple, Optional
from uuid import UUID
from nexus.storage.postgres import PostgresStore


class VectorStore:
    """Vector store using pgvector in PostgreSQL"""
    
    def __init__(self, postgres_store: Optional[PostgresStore] = None):
        self.store = postgres_store or PostgresStore()
    
    def search_similar_claims(self, embedding: List[float], 
                              limit: int = 10,
                              threshold: float = 0.7) -> List[Tuple[UUID, float]]:
        """Search for similar claims"""
        query = """
            SELECT id, 1 - (embedding <=> :embedding::vector) as similarity
            FROM claims
            WHERE 1 - (embedding <=> :embedding::vector) >= :threshold
            ORDER BY embedding <=> :embedding::vector
            LIMIT :limit
        """
        results = self.store.fetch_all(query, {
            "embedding": str(embedding),
            "threshold": threshold,
            "limit": limit
        })
        return [(row[0], row[1]) for row in results]
    
    def search_similar_hypotheses(self, embedding: List[float], 
                                  limit: int = 10,
                                  threshold: float = 0.7) -> List[Tuple[UUID, float]]:
        """Search for similar hypotheses"""
        query = """
            SELECT id, 1 - (embedding <=> :embedding::vector) as similarity
            FROM hypotheses
            WHERE status = 'active'
              AND 1 - (embedding <=> :embedding::vector) >= :threshold
            ORDER BY embedding <=> :embedding::vector
            LIMIT :limit
        """
        results = self.store.fetch_all(query, {
            "embedding": str(embedding),
            "threshold": threshold,
            "limit": limit
        })
        return [(row[0], row[1]) for row in results]
    
    def compute_relevance(self, claim_embedding: List[float], 
                         hypothesis_embedding: List[float]) -> float:
        """Compute cosine similarity between claim and hypothesis"""
        query = """
            SELECT 1 - (:claim_emb::vector <=> :hyp_emb::vector) as similarity
        """
        result = self.store.fetch_one(query, {
            "claim_emb": str(claim_embedding),
            "hyp_emb": str(hypothesis_embedding)
        })
        return result[0] if result else 0.0
