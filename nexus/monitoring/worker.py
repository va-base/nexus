"""Worker process for monitoring flows"""
import time
import threading
from nexus.storage.redis_bus import RedisEventBus
from nexus.extraction.claim_extractor import ClaimExtractor
from nexus.belief.engine import BeliefEngine
from nexus.belief.escalation import EscalationManager


def process_ingestion_events():
    """Process ingestion events"""
    bus = RedisEventBus()
    extractor = ClaimExtractor()
    
    def handle_ingestion(event):
        """Handle ingestion event"""
        evidence_id = event.get("evidence_id")
        content = event.get("content", {}).get("text", "")
        company_id = event.get("company", {}).get("id")
        
        claim_ids = extractor.extract_from_evidence(
            evidence_id, content, {"company_id": company_id}
        )
        
        bus.publish("evidence.extracted", {
            "evidence_id": evidence_id,
            "company_id": company_id,
            "claim_ids": claim_ids
        })
    
    bus.consume("ingestion.raw", "extractors", "worker-1", handle_ingestion)


def process_evidence_events():
    """Process evidence extraction events"""
    bus = RedisEventBus()
    belief_engine = BeliefEngine()
    escalation_mgr = EscalationManager()
    
    def handle_evidence(event):
        """Handle evidence event"""
        claim_ids = event.get("claim_ids", [])
        company_id = event.get("company_id")
        
        from nexus.storage.postgres import PostgresStore
        store = PostgresStore()
        query = """
            SELECT id FROM hypotheses
            WHERE company_id = :company_id AND status = 'active'
        """
        results = store.fetch_all(query, {"company_id": company_id})
        hypothesis_ids = [row[0] for row in results]
        
        for hypothesis_id in hypothesis_ids:
            update = belief_engine.update_belief(hypothesis_id, claim_ids)
            
            escalation = escalation_mgr.check_escalation(
                hypothesis_id,
                update["delta"],
                update["uncertainty"],
                update["prior_belief"],
                update["posterior_belief"]
            )
            
            if escalation["escalation_required"]:
                investigation_id = escalation_mgr.trigger_investigation(
                    hypothesis_id, escalation
                )
                
                bus.publish("investigation.triggered", {
                    "investigation_id": str(investigation_id),
                    "hypothesis_id": str(hypothesis_id),
                    "priority": escalation["priority"]
                })
    
    bus.consume("evidence.extracted", "belief_updaters", "worker-1", handle_evidence)


if __name__ == "__main__":
    print("Starting Nexus worker...")
    
    ingestion_thread = threading.Thread(target=process_ingestion_events, daemon=True)
    evidence_thread = threading.Thread(target=process_evidence_events, daemon=True)
    
    ingestion_thread.start()
    evidence_thread.start()
    
    print("Worker threads started:")
    print("  - Ingestion event processor (ingestion.raw -> evidence.extracted)")
    print("  - Evidence event processor (evidence.extracted -> belief updates)")
    
    try:
        ingestion_thread.join()
        evidence_thread.join()
    except KeyboardInterrupt:
        print("\nShutting down worker...")
        exit(0)
