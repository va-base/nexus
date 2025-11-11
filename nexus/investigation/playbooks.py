"""Base investigation playbook"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from uuid import UUID
from nexus.storage.postgres import PostgresStore


class InvestigationPlaybook(ABC):
    """Base class for investigation playbooks"""
    
    def __init__(self, postgres_store: Optional[PostgresStore] = None):
        self.store = postgres_store or PostgresStore()
    
    @abstractmethod
    def execute(self, investigation_id: UUID, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the investigation playbook"""
        pass
    
    @abstractmethod
    def get_playbook_name(self) -> str:
        """Get playbook name"""
        pass
    
    def update_investigation_status(self, investigation_id: UUID, status: str, outputs: Optional[Dict[str, Any]] = None):
        """Update investigation status"""
        query = """
            UPDATE investigations
            SET status = :status, outputs = :outputs, completed_at = NOW()
            WHERE id = :id
        """
        import json
        self.store.execute(query, {
            "id": str(investigation_id),
            "status": status,
            "outputs": json.dumps(outputs) if outputs else None
        })
