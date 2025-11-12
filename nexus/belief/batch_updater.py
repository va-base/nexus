"""Batch belief update processor"""
from typing import Dict, List, Set
from uuid import UUID
from collections import defaultdict
from nexus.belief.engine import BeliefEngine
from nexus.storage.postgres import PostgresStore


class BatchBeliefUpdater:
    """Process belief updates in batches to reduce write amplification"""
    
    def __init__(self, belief_engine: BeliefEngine = None):
        self.engine = belief_engine or BeliefEngine()
        self.pending_updates: Dict[UUID, Set[UUID]] = defaultdict(set)
    
    def add_claim(self, hypothesis_id: UUID, claim_id: UUID):
        """Add a claim to the batch for a hypothesis"""
        self.pending_updates[hypothesis_id].add(claim_id)
    
    def process_batch(self, trigger_reason: str = "batch_update") -> Dict[UUID, Dict]:
        """Process all pending updates in batch"""
        results = {}
        
        for hypothesis_id, claim_ids in self.pending_updates.items():
            if claim_ids:
                result = self.engine.update_belief(
                    hypothesis_id,
                    list(claim_ids),
                    trigger_reason=trigger_reason
                )
                results[hypothesis_id] = result
        
        self.pending_updates.clear()
        return results
    
    def should_flush(self, max_batch_size: int = 100, 
                    max_hypotheses: int = 50) -> bool:
        """Check if batch should be flushed"""
        total_claims = sum(len(claims) for claims in self.pending_updates.values())
        return (total_claims >= max_batch_size or 
                len(self.pending_updates) >= max_hypotheses)
    
    def get_pending_count(self) -> int:
        """Get total number of pending claims"""
        return sum(len(claims) for claims in self.pending_updates.values())
