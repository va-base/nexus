"""Escalation management"""
from typing import Dict, Any, Optional
from uuid import UUID
from nexus.storage.postgres import PostgresStore
from nexus.config import settings


class EscalationManager:
    """Manage belief update escalations"""
    
    def __init__(self, postgres_store: Optional[PostgresStore] = None):
        self.store = postgres_store or PostgresStore()
        self.delta_threshold = settings.escalation_delta_threshold
        self.uncertainty_threshold = settings.escalation_uncertainty_threshold
    
    def check_escalation(self, hypothesis_id: UUID, delta: float, 
                        uncertainty: float, prior_belief: float,
                        posterior_belief: float) -> Dict[str, Any]:
        """Check if escalation is required"""
        escalation_required = False
        priority = "low"
        reasons = []
        
        if abs(delta) >= self.delta_threshold:
            escalation_required = True
            reasons.append(f"Large belief shift: {delta:.2f}")
            
            if abs(delta) >= 1.0:
                priority = "critical"
            elif abs(delta) >= 0.5:
                priority = "high"
        
        if uncertainty >= self.uncertainty_threshold:
            escalation_required = True
            reasons.append(f"High uncertainty: {uncertainty:.2f}")
            if priority == "low":
                priority = "medium"
        
        if (prior_belief < 0.5 and posterior_belief > 0.5) or \
           (prior_belief > 0.5 and posterior_belief < 0.5):
            if uncertainty < 0.3:  # High confidence flip
                escalation_required = True
                reasons.append("High-confidence conviction flip")
                priority = "high"
        
        if posterior_belief >= 0.9 or posterior_belief <= 0.1:
            escalation_required = True
            reasons.append(f"Extreme conviction: {posterior_belief:.2f}")
            if priority in ["low", "medium"]:
                priority = "high"
        
        return {
            "escalation_required": escalation_required,
            "priority": priority,
            "reasons": reasons
        }
    
    def trigger_investigation(self, hypothesis_id: UUID, 
                            escalation_info: Dict[str, Any]) -> UUID:
        """Trigger an investigation based on escalation"""
        query = """
            SELECT company_id, statement, hypothesis_type
            FROM hypotheses WHERE id = :id
        """
        result = self.store.fetch_one(query, {"id": str(hypothesis_id)})
        if not result:
            raise ValueError(f"Hypothesis {hypothesis_id} not found")
        
        company_id, statement, hypothesis_type = result
        
        investigation_type = "custom"
        if "earnings" in statement.lower() or "revenue" in statement.lower():
            investigation_type = "earnings_deep_dive"
        elif "hiring" in statement.lower() or "headcount" in statement.lower():
            investigation_type = "hiring_momentum"
        
        investigation_data = {
            "hypothesis_id": str(hypothesis_id),
            "company_id": str(company_id) if company_id else None,
            "investigation_type": investigation_type,
            "trigger_reason": "; ".join(escalation_info["reasons"]),
            "priority": escalation_info["priority"],
            "status": "pending",
            "inputs": {
                "hypothesis_id": str(hypothesis_id),
                "trigger_type": "belief_escalation"
            }
        }
        
        investigation_id = self.store.insert_investigation(investigation_data)
        return investigation_id
