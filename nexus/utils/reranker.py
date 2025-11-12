"""Re-ranking utilities using cross-encoder models"""
from typing import List, Tuple, Optional
from uuid import UUID
from sentence_transformers import CrossEncoder
from nexus.storage.postgres import PostgresStore


class Reranker:
    """Re-rank search results using cross-encoder"""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
                 postgres_store: Optional[PostgresStore] = None):
        self.model = CrossEncoder(model_name)
        self.store = postgres_store or PostgresStore()
    
    def rerank_claims(self, query_text: str, claim_ids: List[UUID],
                     top_k: int = 10) -> List[Tuple[UUID, float]]:
        """Re-rank claims using cross-encoder"""
        if not claim_ids:
            return []
        
        claim_texts = self._fetch_claim_texts(claim_ids)
        
        pairs = [(query_text, text) for text in claim_texts.values()]
        scores = self.model.predict(pairs)
        
        results = [(claim_id, float(score)) 
                   for claim_id, score in zip(claim_ids, scores)]
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]
    
    def rerank_hypotheses(self, query_text: str, hypothesis_ids: List[UUID],
                         top_k: int = 10) -> List[Tuple[UUID, float]]:
        """Re-rank hypotheses using cross-encoder"""
        if not hypothesis_ids:
            return []
        
        hypothesis_texts = self._fetch_hypothesis_texts(hypothesis_ids)
        
        pairs = [(query_text, text) for text in hypothesis_texts.values()]
        scores = self.model.predict(pairs)
        
        results = [(hyp_id, float(score)) 
                   for hyp_id, score in zip(hypothesis_ids, scores)]
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]
    
    def _fetch_claim_texts(self, claim_ids: List[UUID]) -> dict:
        """Fetch claim texts from database"""
        if not claim_ids:
            return {}
        
        placeholders = ','.join([f"'{str(cid)}'" for cid in claim_ids])
        query = f"""
            SELECT id, claim_text
            FROM claims
            WHERE id IN ({placeholders})
        """
        results = self.store.fetch_all(query)
        return {row[0]: row[1] for row in results}
    
    def _fetch_hypothesis_texts(self, hypothesis_ids: List[UUID]) -> dict:
        """Fetch hypothesis texts from database"""
        if not hypothesis_ids:
            return {}
        
        placeholders = ','.join([f"'{str(hid)}'" for hid in hypothesis_ids])
        query = f"""
            SELECT id, statement
            FROM hypotheses
            WHERE id IN ({placeholders})
        """
        results = self.store.fetch_all(query)
        return {row[0]: row[1] for row in results}
