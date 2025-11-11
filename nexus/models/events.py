"""Event models for Nexus"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class IngestionEvent(BaseModel):
    """Raw data ingestion event"""
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = "ingestion.raw"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: Dict[str, Any]
    company: Dict[str, str]
    content: Dict[str, Any]
    content_hash: str
    ingested_by: str


class EvidenceEvent(BaseModel):
    """Evidence extraction event"""
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = "evidence.extracted"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    evidence_id: UUID
    company_id: Optional[UUID] = None
    claims: List[Dict[str, Any]]
    model_version: str
    extraction_metadata: Dict[str, Any]


class BeliefUpdateEvent(BaseModel):
    """Belief update event"""
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = "belief.updated"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    hypothesis_id: UUID
    prior_belief: float
    posterior_belief: float
    log_odds_delta: float
    contributing_claims: List[Dict[str, Any]]
    uncertainty: float
    trigger_reason: str
    escalation_required: bool


class InvestigationEvent(BaseModel):
    """Investigation triggered event"""
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = "investigation.triggered"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    investigation_id: UUID
    hypothesis_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    investigation_type: str
    trigger_reason: str
    priority: str


class AlertEvent(BaseModel):
    """Alert fired event"""
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = "alert.fired"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    alert_type: str
    severity: str
    entity_type: str
    entity_id: UUID
    message: str
    metadata: Dict[str, Any]
