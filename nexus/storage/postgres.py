"""PostgreSQL storage adapter"""
import hashlib
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from nexus.config import settings


class PostgresStore:
    """PostgreSQL storage adapter"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(self.database_url, poolclass=NullPool)
    
    def execute(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Execute a query"""
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            conn.commit()
            return result
    
    def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Fetch one row"""
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            return result.fetchone()
    
    def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Fetch all rows"""
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            return result.fetchall()
    
    def insert_company(self, company: Dict[str, Any]) -> UUID:
        """Insert a company"""
        query = """
            INSERT INTO companies (ticker, name, sector, market_cap, is_public, metadata)
            VALUES (:ticker, :name, :sector, :market_cap, :is_public, :metadata)
            RETURNING id
        """
        result = self.execute(query, {
            "ticker": company.get("ticker"),
            "name": company["name"],
            "sector": company.get("sector"),
            "market_cap": company.get("market_cap"),
            "is_public": company.get("is_public", True),
            "metadata": json.dumps(company.get("metadata", {}))
        })
        return result.fetchone()[0]
    
    def insert_hypothesis(self, hypothesis: Dict[str, Any]) -> UUID:
        """Insert a hypothesis"""
        embedding = hypothesis.get("embedding")
        embedding_str = str(embedding) if embedding else None
        
        query = """
            INSERT INTO hypotheses (company_id, theme_id, statement, hypothesis_type, 
                                   time_horizon, target_date, initial_belief, embedding, 
                                   metadata, created_by)
            VALUES (:company_id, :theme_id, :statement, :hypothesis_type, 
                    :time_horizon, :target_date, :initial_belief, :embedding::vector, 
                    :metadata, :created_by)
            RETURNING id
        """
        result = self.execute(query, {
            "company_id": hypothesis.get("company_id"),
            "theme_id": hypothesis.get("theme_id"),
            "statement": hypothesis["statement"],
            "hypothesis_type": hypothesis.get("hypothesis_type"),
            "time_horizon": hypothesis.get("time_horizon"),
            "target_date": hypothesis.get("target_date"),
            "initial_belief": hypothesis.get("initial_belief", 0.5),
            "embedding": embedding_str,
            "metadata": json.dumps(hypothesis.get("metadata", {})),
            "created_by": hypothesis.get("created_by", "system")
        })
        return result.fetchone()[0]
    
    def insert_evidence(self, evidence: Dict[str, Any]) -> UUID:
        """Insert evidence"""
        content_hash = hashlib.sha256(evidence["content"].encode()).hexdigest()
        
        query = """
            INSERT INTO evidence (company_id, source_type, source_url, source_date, 
                                 title, content, content_hash, raw_metadata, 
                                 validation_status, ingested_by)
            VALUES (:company_id, :source_type, :source_url, :source_date, 
                    :title, :content, :content_hash, :raw_metadata, 
                    :validation_status, :ingested_by)
            RETURNING id
        """
        result = self.execute(query, {
            "company_id": evidence.get("company_id"),
            "source_type": evidence["source_type"],
            "source_url": evidence.get("source_url"),
            "source_date": evidence.get("source_date"),
            "title": evidence.get("title"),
            "content": evidence["content"],
            "content_hash": content_hash,
            "raw_metadata": json.dumps(evidence.get("raw_metadata", {})),
            "validation_status": evidence.get("validation_status", "pending"),
            "ingested_by": evidence.get("ingested_by", "system")
        })
        return result.fetchone()[0]
    
    def insert_claim(self, claim: Dict[str, Any]) -> UUID:
        """Insert a claim"""
        embedding = claim.get("embedding")
        embedding_str = str(embedding) if embedding else None
        
        query = """
            INSERT INTO claims (evidence_id, company_id, claim_text, claim_type, 
                               polarity, magnitude, confidence, extracted_entities, 
                               embedding, model_version)
            VALUES (:evidence_id, :company_id, :claim_text, :claim_type, 
                    :polarity, :magnitude, :confidence, :extracted_entities, 
                    :embedding::vector, :model_version)
            RETURNING id
        """
        result = self.execute(query, {
            "evidence_id": claim["evidence_id"],
            "company_id": claim.get("company_id"),
            "claim_text": claim["claim_text"],
            "claim_type": claim.get("claim_type"),
            "polarity": claim.get("polarity"),
            "magnitude": claim.get("magnitude"),
            "confidence": claim.get("confidence"),
            "extracted_entities": json.dumps(claim.get("extracted_entities", {})),
            "embedding": embedding_str,
            "model_version": claim.get("model_version")
        })
        return result.fetchone()[0]
    
    def insert_belief_update(self, update: Dict[str, Any]) -> UUID:
        """Insert a belief update"""
        query = """
            INSERT INTO belief_updates (hypothesis_id, prior_belief, posterior_belief, 
                                       log_odds_delta, contributing_claims, reliability_score,
                                       recency_score, relevance_score, uncertainty, 
                                       trigger_reason, created_by)
            VALUES (:hypothesis_id, :prior_belief, :posterior_belief, 
                    :log_odds_delta, :contributing_claims, :reliability_score,
                    :recency_score, :relevance_score, :uncertainty, 
                    :trigger_reason, :created_by)
            RETURNING id
        """
        result = self.execute(query, {
            "hypothesis_id": update["hypothesis_id"],
            "prior_belief": update["prior_belief"],
            "posterior_belief": update["posterior_belief"],
            "log_odds_delta": update["log_odds_delta"],
            "contributing_claims": json.dumps(update.get("contributing_claims", [])),
            "reliability_score": update.get("reliability_score"),
            "recency_score": update.get("recency_score"),
            "relevance_score": update.get("relevance_score"),
            "uncertainty": update.get("uncertainty"),
            "trigger_reason": update.get("trigger_reason"),
            "created_by": update.get("created_by", "system")
        })
        return result.fetchone()[0]
    
    def get_current_belief(self, hypothesis_id: UUID) -> Optional[Dict[str, Any]]:
        """Get current belief for a hypothesis"""
        query = """
            SELECT posterior_belief, log_odds_delta, uncertainty, created_at
            FROM belief_updates
            WHERE hypothesis_id = :hypothesis_id
            ORDER BY created_at DESC
            LIMIT 1
        """
        result = self.fetch_one(query, {"hypothesis_id": str(hypothesis_id)})
        if result:
            return {
                "belief": result[0],
                "log_odds_delta": result[1],
                "uncertainty": result[2],
                "last_updated": result[3]
            }
        return None
    
    def get_active_hypotheses(self) -> List[Dict[str, Any]]:
        """Get all active hypotheses"""
        query = """
            SELECT id, company_id, statement, hypothesis_type, embedding
            FROM hypotheses
            WHERE status = 'active'
        """
        results = self.fetch_all(query)
        return [
            {
                "id": row[0],
                "company_id": row[1],
                "statement": row[2],
                "hypothesis_type": row[3],
                "embedding": row[4]
            }
            for row in results
        ]
    
    def insert_investigation(self, investigation: Dict[str, Any]) -> UUID:
        """Insert an investigation"""
        query = """
            INSERT INTO investigations (hypothesis_id, company_id, investigation_type, 
                                       trigger_reason, priority, status, inputs)
            VALUES (:hypothesis_id, :company_id, :investigation_type, 
                    :trigger_reason, :priority, :status, :inputs)
            RETURNING id
        """
        result = self.execute(query, {
            "hypothesis_id": investigation.get("hypothesis_id"),
            "company_id": investigation.get("company_id"),
            "investigation_type": investigation["investigation_type"],
            "trigger_reason": investigation.get("trigger_reason"),
            "priority": investigation.get("priority", "medium"),
            "status": investigation.get("status", "pending"),
            "inputs": json.dumps(investigation.get("inputs", {}))
        })
        return result.fetchone()[0]
    
    def log_provenance(self, event: Dict[str, Any]) -> UUID:
        """Log provenance event"""
        query = """
            INSERT INTO provenance_log (event_type, entity_type, entity_id, action, 
                                       actor, payload, content_hash, parent_event_id)
            VALUES (:event_type, :entity_type, :entity_id, :action, 
                    :actor, :payload, :content_hash, :parent_event_id)
            RETURNING id
        """
        result = self.execute(query, {
            "event_type": event["event_type"],
            "entity_type": event["entity_type"],
            "entity_id": str(event["entity_id"]),
            "action": event["action"],
            "actor": event.get("actor", "system"),
            "payload": json.dumps(event.get("payload", {})),
            "content_hash": event.get("content_hash"),
            "parent_event_id": event.get("parent_event_id")
        })
        return result.fetchone()[0]
    
    def log_llm_interaction(self, interaction: Dict[str, Any]) -> UUID:
        """Log LLM interaction"""
        prompt_hash = hashlib.sha256(interaction["prompt_text"].encode()).hexdigest()
        
        query = """
            INSERT INTO llm_interactions (request_id, model_name, prompt_template, 
                                         prompt_text, prompt_hash, response_text, 
                                         response_metadata, tokens_used, latency_ms, 
                                         error, redacted_fields)
            VALUES (:request_id, :model_name, :prompt_template, 
                    :prompt_text, :prompt_hash, :response_text, 
                    :response_metadata, :tokens_used, :latency_ms, 
                    :error, :redacted_fields)
            RETURNING id
        """
        result = self.execute(query, {
            "request_id": interaction["request_id"],
            "model_name": interaction["model_name"],
            "prompt_template": interaction.get("prompt_template"),
            "prompt_text": interaction["prompt_text"],
            "prompt_hash": prompt_hash,
            "response_text": interaction.get("response_text"),
            "response_metadata": json.dumps(interaction.get("response_metadata", {})),
            "tokens_used": interaction.get("tokens_used"),
            "latency_ms": interaction.get("latency_ms"),
            "error": interaction.get("error"),
            "redacted_fields": json.dumps(interaction.get("redacted_fields", {}))
        })
        return result.fetchone()[0]
