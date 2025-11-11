"""Claim extraction orchestrator"""
import time
import uuid
from typing import Dict, Any, List, Optional
from nexus.extraction.llm_client import get_llm_client
from nexus.utils.embeddings import EmbeddingGenerator
from nexus.storage.postgres import PostgresStore
from nexus.ingestion.mnpi_filter import MNPIFilter


class ClaimExtractor:
    """Extract and store claims from evidence"""
    
    def __init__(self, 
                 llm_client: Optional[Any] = None,
                 embedding_generator: Optional[EmbeddingGenerator] = None,
                 postgres_store: Optional[PostgresStore] = None):
        self.llm_client = llm_client or get_llm_client()
        self.embedding_gen = embedding_generator or EmbeddingGenerator()
        self.store = postgres_store or PostgresStore()
        self.mnpi_filter = MNPIFilter()
    
    def extract_from_evidence(self, evidence_id: str, content: str, 
                             context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Extract claims from evidence and store them"""
        start_time = time.time()
        
        redacted_content, redacted_fields = self.mnpi_filter.redact_pii(content)
        
        claims = self.llm_client.extract_claims(redacted_content, context)
        
        claim_texts = [claim["claim_text"] for claim in claims]
        embeddings = self.embedding_gen.encode_batch(claim_texts) if claim_texts else []
        
        claim_ids = []
        for claim, embedding in zip(claims, embeddings):
            claim["evidence_id"] = evidence_id
            claim["company_id"] = context.get("company_id") if context else None
            claim["embedding"] = embedding
            claim["model_version"] = self.llm_client.get_model_name()
            
            claim_id = self.store.insert_claim(claim)
            claim_ids.append(str(claim_id))
        
        latency_ms = int((time.time() - start_time) * 1000)
        self.store.log_llm_interaction({
            "request_id": str(uuid.uuid4()),
            "model_name": self.llm_client.get_model_name(),
            "prompt_template": "claim_extraction",
            "prompt_text": redacted_content[:1000],  # Store first 1000 chars
            "response_text": str(claims),
            "response_metadata": {"claim_count": len(claims)},
            "tokens_used": len(redacted_content.split()) + len(str(claims).split()),
            "latency_ms": latency_ms,
            "redacted_fields": redacted_fields
        })
        
        return claim_ids
