"""Mock claim extractor for testing"""
import re
from typing import Dict, Any, List, Optional
from nexus.extraction.llm_client import LLMClient


class MockExtractor(LLMClient):
    """Deterministic mock extractor for testing"""
    
    def extract_claims(self, text: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Extract claims using rule-based patterns"""
        claims = []
        
        revenue_patterns = [
            r'revenue\s+(?:of|was|grew to)\s+\$?([\d.]+)\s*(billion|million)',
            r'(?:generated|reported)\s+\$?([\d.]+)\s*(billion|million)\s+in revenue',
        ]
        
        for pattern in revenue_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = float(match.group(1))
                unit = match.group(2).lower()
                value_millions = value * 1000 if unit == "billion" else value
                
                claims.append({
                    "claim_text": match.group(0),
                    "claim_type": "financial",
                    "polarity": "positive",
                    "magnitude": 0.7,
                    "confidence": 0.9,
                    "extracted_entities": {
                        "metric": "revenue",
                        "value": value_millions,
                        "unit": "millions"
                    }
                })
        
        growth_patterns = [
            r'([\d.]+)%\s+(?:growth|increase|yoy)',
            r'grew\s+(?:by\s+)?([\d.]+)%',
        ]
        
        for pattern in growth_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                growth_rate = float(match.group(1)) / 100
                
                claims.append({
                    "claim_text": match.group(0),
                    "claim_type": "financial",
                    "polarity": "positive" if growth_rate > 0 else "negative",
                    "magnitude": min(abs(growth_rate) / 0.5, 1.0),  # Normalize to 0-1
                    "confidence": 0.85,
                    "extracted_entities": {
                        "metric": "growth_rate",
                        "value": growth_rate
                    }
                })
        
        hiring_patterns = [
            r'hiring\s+([\d,]+)\s+(?:new\s+)?(?:employees|people)',
            r'([\d,]+)\s+new\s+(?:job\s+)?(?:openings|positions)',
        ]
        
        for pattern in hiring_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                count = int(match.group(1).replace(',', ''))
                
                claims.append({
                    "claim_text": match.group(0),
                    "claim_type": "operational",
                    "polarity": "positive",
                    "magnitude": min(count / 100, 1.0),  # Normalize
                    "confidence": 0.8,
                    "extracted_entities": {
                        "metric": "hiring_count",
                        "value": count
                    }
                })
        
        sentiment_patterns = [
            (r'strong\s+(?:demand|performance|growth)', "positive", 0.7),
            (r'weak\s+(?:demand|performance|growth)', "negative", 0.7),
            (r'challenging\s+(?:environment|market|conditions)', "negative", 0.6),
            (r'optimistic\s+(?:about|outlook)', "positive", 0.6),
        ]
        
        for pattern, polarity, magnitude in sentiment_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                claims.append({
                    "claim_text": match.group(0),
                    "claim_type": "sentiment",
                    "polarity": polarity,
                    "magnitude": magnitude,
                    "confidence": 0.75,
                    "extracted_entities": {}
                })
        
        return claims
    
    def get_model_name(self) -> str:
        """Get model name"""
        return "mock-extractor-v1"
