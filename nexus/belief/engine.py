"""Belief update engine"""
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import date
from nexus.belief.scoring import BeliefScorer
from nexus.storage.postgres import PostgresStore
from nexus.storage.vector_store import VectorStore
from nexus.config import settings


class BeliefEngine:
    """Update beliefs based on new evidence"""
    
    def __init__(self, 
                 postgres_store: Optional[PostgresStore] = None,
                 vector_store: Optional[VectorStore] = None,
                 scorer: Optional[BeliefScorer] = None):
        self.store = postgres_store or PostgresStore()
        self.vector_store = vector_store or VectorStore(self.store)
        self.scorer = scorer or BeliefScorer()
    
    def update_belief(self, hypothesis_id: UUID, new_claim_ids: List[UUID],
                     trigger_reason: str = "new_evidence") -> Dict[str, Any]:
        """Update belief for a hypothesis based on new claims"""
        current = self.store.get_current_belief(hypothesis_id)
        if current is None:
            query = "SELECT initial_belief FROM hypotheses WHERE id = :id"
            result = self.store.fetch_one(query, {"id": str(hypothesis_id)})
            prior_belief = result[0] if result else 0.5
            current_logit = self.scorer.log_odds(prior_belief)
        else:
            prior_belief = current["belief"]
            current_logit = self.scorer.log_odds(prior_belief)
        
        query = "SELECT embedding FROM hypotheses WHERE id = :id"
        result = self.store.fetch_one(query, {"id": str(hypothesis_id)})
        hypothesis_embedding = result[0] if result else None
        
        delta_logit = 0
        contributions = []
        
        for claim_id in new_claim_ids:
            query = """
                SELECT claim_text, claim_type, polarity, magnitude, confidence,
                       embedding, evidence_id
                FROM claims WHERE id = :id
            """
            claim_row = self.store.fetch_one(query, {"id": str(claim_id)})
            if not claim_row:
                continue
            
            claim_text, claim_type, polarity, magnitude, confidence, claim_embedding, evidence_id = claim_row
            
            query = "SELECT source_type, source_date FROM evidence WHERE id = :id"
            evidence_row = self.store.fetch_one(query, {"id": str(evidence_id)})
            if not evidence_row:
                continue
            
            source_type, source_date = evidence_row
            
            if hypothesis_embedding and claim_embedding:
                relevance = self.vector_store.compute_relevance(claim_embedding, hypothesis_embedding)
            else:
                relevance = 0.5  # Default if no embeddings
            
            if relevance < settings.relevance_threshold:
                continue
            
            reliability = self.scorer.compute_reliability(source_type, confidence or 0.8)
            recency = self.scorer.compute_recency(source_date) if source_date else 1.0
            weight = self.scorer.compute_weight(reliability, recency, relevance, magnitude or 0.5)
            
            sign = 1 if polarity == "positive" else (-1 if polarity == "negative" else 0)
            
            delta_logit += sign * weight
            
            contributions.append({
                "claim_id": str(claim_id),
                "weight": weight,
                "sign": sign,
                "reliability": reliability,
                "recency": recency,
                "relevance": relevance
            })
            
            self.store.execute("""
                INSERT INTO hypothesis_claims (hypothesis_id, claim_id, relevance_score, impact_direction)
                VALUES (:hypothesis_id, :claim_id, :relevance_score, :impact_direction)
                ON CONFLICT (hypothesis_id, claim_id) DO NOTHING
            """, {
                "hypothesis_id": str(hypothesis_id),
                "claim_id": str(claim_id),
                "relevance_score": relevance,
                "impact_direction": "supports" if sign > 0 else ("contradicts" if sign < 0 else "neutral")
            })
        
        new_logit = current_logit + delta_logit
        posterior_belief = self.scorer.sigmoid(new_logit)
        
        uncertainty = self.scorer.compute_uncertainty(contributions)
        
        update_data = {
            "hypothesis_id": str(hypothesis_id),
            "prior_belief": prior_belief,
            "posterior_belief": posterior_belief,
            "log_odds_delta": delta_logit,
            "contributing_claims": contributions,
            "reliability_score": sum(c["reliability"] for c in contributions) / len(contributions) if contributions else 0,
            "recency_score": sum(c["recency"] for c in contributions) / len(contributions) if contributions else 0,
            "relevance_score": sum(c["relevance"] for c in contributions) / len(contributions) if contributions else 0,
            "uncertainty": uncertainty,
            "trigger_reason": trigger_reason,
            "created_by": "belief_engine"
        }
        
        update_id = self.store.insert_belief_update(update_data)
        
        self.store.execute("""
            INSERT INTO current_beliefs (hypothesis_id, current_belief, log_odds_delta, uncertainty, last_updated)
            VALUES (:hypothesis_id, :current_belief, :log_odds_delta, :uncertainty, NOW())
            ON CONFLICT (hypothesis_id) 
            DO UPDATE SET 
                current_belief = EXCLUDED.current_belief,
                log_odds_delta = EXCLUDED.log_odds_delta,
                uncertainty = EXCLUDED.uncertainty,
                last_updated = EXCLUDED.last_updated
        """, {
            "hypothesis_id": str(hypothesis_id),
            "current_belief": posterior_belief,
            "log_odds_delta": delta_logit,
            "uncertainty": uncertainty
        })
        
        return {
            "update_id": update_id,
            "prior_belief": prior_belief,
            "posterior_belief": posterior_belief,
            "delta": delta_logit,
            "uncertainty": uncertainty,
            "contributions": contributions
        }
