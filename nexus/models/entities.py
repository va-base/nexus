"""Entity models for Nexus"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class Company(BaseModel):
    """Company entity"""
    id: Optional[UUID] = None
    ticker: Optional[str] = None
    name: str
    sector: Optional[str] = None
    market_cap: Optional[int] = None
    is_public: bool = True
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Instrument(BaseModel):
    """Tradable instrument"""
    id: Optional[UUID] = None
    company_id: UUID
    symbol: str
    instrument_type: str  # stock, option, bond
    exchange: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


class Theme(BaseModel):
    """Investment theme"""
    id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    parent_theme_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


class Hypothesis(BaseModel):
    """Investment hypothesis"""
    id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    theme_id: Optional[UUID] = None
    statement: str
    hypothesis_type: Optional[str] = None  # growth, margin, market_share, product, risk
    time_horizon: Optional[str] = None  # short_term, medium_term, long_term
    target_date: Optional[date] = None
    initial_belief: float = 0.5
    status: str = "active"  # active, resolved, archived
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None


class Evidence(BaseModel):
    """Evidence artifact"""
    id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    source_type: str  # filing, transcript, news, hiring, manual
    source_url: Optional[str] = None
    source_date: Optional[date] = None
    title: Optional[str] = None
    content: str
    content_hash: str
    raw_metadata: Optional[Dict[str, Any]] = None
    validation_status: str = "pending"  # pending, validated, rejected, mnpi_hold
    validation_errors: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    ingested_by: Optional[str] = None


class Claim(BaseModel):
    """Extracted claim"""
    id: Optional[UUID] = None
    evidence_id: UUID
    company_id: Optional[UUID] = None
    claim_text: str
    claim_type: Optional[str] = None  # financial, operational, strategic, risk, sentiment
    polarity: Optional[str] = None  # positive, negative, neutral
    magnitude: Optional[float] = None  # 0.0 to 1.0
    confidence: Optional[float] = None  # 0.0 to 1.0
    extracted_entities: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None
    model_version: Optional[str] = None
    created_at: Optional[datetime] = None


class HypothesisClaim(BaseModel):
    """Link between hypothesis and claim"""
    id: Optional[UUID] = None
    hypothesis_id: UUID
    claim_id: UUID
    relevance_score: float
    impact_direction: Optional[str] = None  # supports, contradicts, neutral
    created_at: Optional[datetime] = None


class BeliefUpdate(BaseModel):
    """Belief update record"""
    id: Optional[UUID] = None
    hypothesis_id: UUID
    prior_belief: float
    posterior_belief: float
    log_odds_delta: float
    contributing_claims: Optional[List[Dict[str, Any]]] = None
    reliability_score: Optional[float] = None
    recency_score: Optional[float] = None
    relevance_score: Optional[float] = None
    uncertainty: Optional[float] = None
    trigger_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None


class Memo(BaseModel):
    """Research memo"""
    id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    theme_id: Optional[UUID] = None
    title: str
    content: str
    memo_type: Optional[str] = None  # deep_dive, update, alert, investigation
    author: Optional[str] = None
    related_hypotheses: Optional[List[UUID]] = None
    related_evidence: Optional[List[UUID]] = None
    embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Prediction(BaseModel):
    """Quantitative prediction"""
    id: Optional[UUID] = None
    hypothesis_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    metric_name: str
    predicted_value: float
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None
    prediction_date: date
    target_date: date
    model_version: Optional[str] = None
    actual_value: Optional[float] = None
    actual_date: Optional[date] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


class Position(BaseModel):
    """Investment position"""
    id: Optional[UUID] = None
    instrument_id: UUID
    position_type: str  # long, short
    quantity: float
    entry_price: Optional[float] = None
    entry_date: Optional[date] = None
    exit_price: Optional[float] = None
    exit_date: Optional[date] = None
    status: str = "open"  # open, closed
    related_hypotheses: Optional[List[UUID]] = None
    rationale: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Investigation(BaseModel):
    """Investigation record"""
    id: Optional[UUID] = None
    hypothesis_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    investigation_type: str  # earnings_deep_dive, hiring_momentum, custom
    trigger_reason: Optional[str] = None
    priority: str = "medium"  # low, medium, high, critical
    status: str = "pending"  # pending, in_progress, completed, cancelled
    assigned_to: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
