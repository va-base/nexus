"""Configuration management for Nexus"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    database_url: str = "postgresql://nexus:nexus_dev_password@localhost:5432/nexus"
    
    redis_url: str = "redis://localhost:6379"
    
    prefect_api_url: str = "http://localhost:4200/api"
    
    llm_backend: str = "mock"  # mock, openai, anthropic
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    data_dir: str = "/app/data"
    parquet_dir: str = "/app/data/parquet"
    fixtures_dir: str = "/app/data/fixtures"
    
    log_level: str = "INFO"
    
    belief_decay_lambda: float = 0.01  # half-life ~70 days
    relevance_threshold: float = 0.7
    escalation_delta_threshold: float = 0.5
    escalation_uncertainty_threshold: float = 0.4
    
    reliability_sec_filing: float = 0.95
    reliability_earnings_transcript: float = 0.90
    reliability_news_tier1: float = 0.75
    reliability_social_media: float = 0.40
    reliability_manual: float = 0.85
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
