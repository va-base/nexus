"""LLM client abstraction"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from nexus.config import settings


class LLMClient(ABC):
    """Abstract LLM client"""
    
    @abstractmethod
    def extract_claims(self, text: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Extract claims from text"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get model name"""
        pass


def get_llm_client() -> LLMClient:
    """Get LLM client based on configuration"""
    backend = settings.llm_backend.lower()
    
    if backend == "mock":
        from nexus.extraction.mock_extractor import MockExtractor
        return MockExtractor()
    elif backend == "openai":
        from nexus.extraction.openai_client import OpenAIClient
        return OpenAIClient(api_key=settings.openai_api_key)
    elif backend == "anthropic":
        from nexus.extraction.anthropic_client import AnthropicClient
        return AnthropicClient(api_key=settings.anthropic_api_key)
    else:
        raise ValueError(f"Unknown LLM backend: {backend}")
