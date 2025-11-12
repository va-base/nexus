"""Hybrid retrieval combining vector search and BM25"""
from typing import List, Tuple, Optional, Dict, Any
from uuid import UUID
from nexus.storage.postgres import PostgresStore
from nexus.storage.vector_store import VectorStore


class HybridRetrieval:
    """Hybrid retrieval using vector search + BM25 with RRF"""
    
    def __init__(self, postgres_store: Optional[PostgresStore] = None,
                 vector_store: Optional[VectorStore] = None):
        self.store = postgres_store or PostgresStore()
        self.vector_store = vector_store or VectorStore(self.store)
    
    def search_claims(self, embedding: List[float], query_text: str,
                     limit: int = 20, vector_weight: float = 0.6) -> List[Tuple[UUID, float]]:
        """Hybrid search combining vector similarity and BM25"""
        vector_results = self.vector_store.search_similar_claims(
            embedding, limit=limit * 2, threshold=0.5
        )
        
        bm25_results = self._bm25_search_claims(query_text, limit=limit * 2)
        
        combined = self._reciprocal_rank_fusion(
            vector_results, bm25_results, vector_weight
        )
        
        return combined[:limit]
    
    def search_hypotheses(self, embedding: List[float], query_text: str,
                         limit: int = 20, vector_weight: float = 0.6) -> List[Tuple[UUID, float]]:
        """Hybrid search for hypotheses"""
        vector_results = self.vector_store.search_similar_hypotheses(
            embedding, limit=limit * 2, threshold=0.5
        )
        
        bm25_results = self._bm25_search_hypotheses(query_text, limit=limit * 2)
        
        combined = self._reciprocal_rank_fusion(
            vector_results, bm25_results, vector_weight
        )
        
        return combined[:limit]
    
    def _bm25_search_claims(self, query_text: str, limit: int) -> List[Tuple[UUID, float]]:
        """BM25 full-text search on claims"""
        query = """
            SELECT id, ts_rank(to_tsvector('english', claim_text), 
                              plainto_tsquery('english', :query)) as rank
            FROM claims
            WHERE to_tsvector('english', claim_text) @@ plainto_tsquery('english', :query)
            ORDER BY rank DESC
            LIMIT :limit
        """
        results = self.store.fetch_all(query, {"query": query_text, "limit": limit})
        return [(row[0], float(row[1])) for row in results]
    
    def _bm25_search_hypotheses(self, query_text: str, limit: int) -> List[Tuple[UUID, float]]:
        """BM25 full-text search on hypotheses"""
        query = """
            SELECT id, ts_rank(to_tsvector('english', statement), 
                              plainto_tsquery('english', :query)) as rank
            FROM hypotheses
            WHERE status = 'active'
              AND to_tsvector('english', statement) @@ plainto_tsquery('english', :query)
            ORDER BY rank DESC
            LIMIT :limit
        """
        results = self.store.fetch_all(query, {"query": query_text, "limit": limit})
        return [(row[0], float(row[1])) for row in results]
    
    def _reciprocal_rank_fusion(self, vector_results: List[Tuple[UUID, float]],
                                bm25_results: List[Tuple[UUID, float]],
                                vector_weight: float = 0.6,
                                k: int = 60) -> List[Tuple[UUID, float]]:
        """Combine results using Reciprocal Rank Fusion"""
        scores: Dict[UUID, float] = {}
        
        for rank, (doc_id, _) in enumerate(vector_results, 1):
            scores[doc_id] = scores.get(doc_id, 0) + vector_weight / (k + rank)
        
        bm25_weight = 1.0 - vector_weight
        for rank, (doc_id, _) in enumerate(bm25_results, 1):
            scores[doc_id] = scores.get(doc_id, 0) + bm25_weight / (k + rank)
        
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results
