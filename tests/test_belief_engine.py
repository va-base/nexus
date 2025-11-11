"""Test belief engine"""
import pytest
from nexus.belief.scoring import BeliefScorer
from datetime import date, timedelta


def test_belief_scorer_reliability():
    """Test reliability scoring"""
    scorer = BeliefScorer()
    
    reliability = scorer.compute_reliability("filing", 0.9)
    assert reliability > 0.8
    
    reliability = scorer.compute_reliability("social", 0.9)
    assert reliability < 0.5


def test_belief_scorer_recency():
    """Test recency scoring"""
    scorer = BeliefScorer()
    
    today = date.today()
    yesterday = today - timedelta(days=1)
    old_date = today - timedelta(days=100)
    
    recency_recent = scorer.compute_recency(yesterday, today)
    recency_old = scorer.compute_recency(old_date, today)
    
    assert recency_recent > recency_old
    assert recency_recent > 0.9


def test_log_odds_conversion():
    """Test log-odds conversion"""
    scorer = BeliefScorer()
    
    p = 0.7
    logit = scorer.log_odds(p)
    p_back = scorer.sigmoid(logit)
    
    assert abs(p - p_back) < 0.001


def test_uncertainty_computation():
    """Test uncertainty computation"""
    scorer = BeliefScorer()
    
    contributions = [
        {"weight": 0.8, "sign": 1},
        {"weight": 0.7, "sign": 1},
        {"weight": 0.9, "sign": 1}
    ]
    uncertainty = scorer.compute_uncertainty(contributions)
    assert uncertainty < 0.3
    
    contributions = [
        {"weight": 0.8, "sign": 1},
        {"weight": 0.7, "sign": -1},
        {"weight": 0.9, "sign": 1}
    ]
    uncertainty = scorer.compute_uncertainty(contributions)
    assert uncertainty > 0.3
