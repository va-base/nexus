"""Belief scoring utilities"""
import math
from datetime import datetime, date
from typing import Dict, Any, List
from nexus.config import settings


class BeliefScorer:
    """Compute belief scores and weights"""
    
    def __init__(self):
        self.decay_lambda = settings.belief_decay_lambda
        self.relevance_threshold = settings.relevance_threshold
    
    def compute_reliability(self, source_type: str, confidence: float) -> float:
        """Compute reliability score"""
        base_reliability = {
            "filing": settings.reliability_sec_filing,
            "transcript": settings.reliability_earnings_transcript,
            "news": settings.reliability_news_tier1,
            "social": settings.reliability_social_media,
            "manual": settings.reliability_manual,
        }.get(source_type, 0.5)
        
        return base_reliability * confidence
    
    def compute_recency(self, source_date: date, current_date: date = None) -> float:
        """Compute recency score with exponential decay"""
        if current_date is None:
            current_date = date.today()
        
        delta_days = (current_date - source_date).days
        recency = math.exp(-self.decay_lambda * delta_days)
        return recency
    
    def compute_weight(self, reliability: float, recency: float, 
                      relevance: float, magnitude: float) -> float:
        """Compute overall weight"""
        return reliability * recency * relevance * magnitude
    
    def compute_uncertainty(self, contributions: List[Dict[str, Any]]) -> float:
        """Compute uncertainty from contribution variance"""
        if not contributions:
            return 1.0
        
        weighted_contribs = [c["weight"] * c["sign"] for c in contributions]
        
        if len(weighted_contribs) < 2:
            return 0.5
        
        mean = sum(weighted_contribs) / len(weighted_contribs)
        variance = sum((x - mean) ** 2 for x in weighted_contribs) / len(weighted_contribs)
        std_dev = math.sqrt(variance)
        
        mean_abs_weight = sum(abs(c["weight"]) for c in contributions) / len(contributions)
        
        if mean_abs_weight == 0:
            return 1.0
        
        uncertainty = std_dev / mean_abs_weight
        return min(uncertainty, 1.0)
    
    def log_odds(self, probability: float) -> float:
        """Convert probability to log-odds"""
        p = max(0.001, min(0.999, probability))
        return math.log(p / (1 - p))
    
    def sigmoid(self, log_odds: float) -> float:
        """Convert log-odds to probability"""
        return 1 / (1 + math.exp(-log_odds))
