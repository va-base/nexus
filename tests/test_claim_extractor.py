"""Test claim extractor"""
import pytest
from nexus.extraction.mock_extractor import MockExtractor


def test_mock_extractor_revenue():
    """Test mock extractor revenue extraction"""
    extractor = MockExtractor()
    
    text = "Revenue of $150 million"
    claims = extractor.extract_claims(text)
    
    assert len(claims) > 0
    assert any(c["claim_type"] == "financial" for c in claims)
    assert any("revenue" in c.get("extracted_entities", {}).get("metric", "") for c in claims)


def test_mock_extractor_growth():
    """Test mock extractor growth extraction"""
    extractor = MockExtractor()
    
    text = "Revenue grew 35% year over year"
    claims = extractor.extract_claims(text)
    
    assert len(claims) > 0
    growth_claims = [c for c in claims if c.get("extracted_entities", {}).get("metric") == "growth_rate"]
    assert len(growth_claims) > 0


def test_mock_extractor_sentiment():
    """Test mock extractor sentiment extraction"""
    extractor = MockExtractor()
    
    text = "We are optimistic about the future and see strong demand"
    claims = extractor.extract_claims(text)
    
    assert len(claims) > 0
    sentiment_claims = [c for c in claims if c["claim_type"] == "sentiment"]
    assert len(sentiment_claims) > 0
    assert all(c["polarity"] == "positive" for c in sentiment_claims)
