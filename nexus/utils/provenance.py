"""Provenance logging utilities"""
from typing import Dict, Any, Optional
from uuid import UUID
from nexus.storage.postgres import PostgresStore


class ProvenanceLogger:
    """Log provenance events"""
    
    def __init__(self, postgres_store: Optional[PostgresStore] = None):
        self.store = postgres_store or PostgresStore()
    
    def log_event(self, event_type: str, entity_type: str, entity_id: UUID,
                  action: str, actor: str = "system",
                  payload: Optional[Dict[str, Any]] = None,
                  content_hash: Optional[str] = None,
                  parent_event_id: Optional[UUID] = None) -> UUID:
        """Log a provenance event"""
        event = {
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "actor": actor,
            "payload": payload,
            "content_hash": content_hash,
            "parent_event_id": parent_event_id
        }
        return self.store.log_provenance(event)
    
    def log_ingestion(self, evidence_id: UUID, source_type: str,
                     content_hash: str, actor: str = "system") -> UUID:
        """Log evidence ingestion"""
        return self.log_event(
            event_type="evidence.ingested",
            entity_type="evidence",
            entity_id=evidence_id,
            action="ingest",
            actor=actor,
            content_hash=content_hash
        )
    
    def log_extraction(self, claim_id: UUID, evidence_id: UUID,
                      model_version: str, parent_event_id: UUID) -> UUID:
        """Log claim extraction"""
        return self.log_event(
            event_type="claim.extracted",
            entity_type="claim",
            entity_id=claim_id,
            action="extract",
            actor=f"llm:{model_version}",
            payload={"evidence_id": str(evidence_id)},
            parent_event_id=parent_event_id
        )
    
    def log_belief_update(self, update_id: UUID, hypothesis_id: UUID,
                         delta: float, parent_event_id: Optional[UUID] = None) -> UUID:
        """Log belief update"""
        return self.log_event(
            event_type="belief.updated",
            entity_type="belief_update",
            entity_id=update_id,
            action="update",
            payload={"hypothesis_id": str(hypothesis_id), "delta": delta},
            parent_event_id=parent_event_id
        )
