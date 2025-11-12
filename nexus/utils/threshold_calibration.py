"""Threshold calibration utilities for retrieval and belief updates"""
from typing import List, Tuple, Optional, Dict
from uuid import UUID
import numpy as np
from nexus.storage.postgres import PostgresStore


class ThresholdCalibrator:
    """Calibrate retrieval and belief update thresholds based on evaluation data"""
    
    def __init__(self, postgres_store: Optional[PostgresStore] = None):
        self.store = postgres_store or PostgresStore()
    
    def calibrate_relevance_threshold(self, 
                                     evaluation_data: List[Tuple[float, bool]],
                                     target_precision: float = 0.9) -> float:
        """
        Calibrate relevance threshold to achieve target precision
        
        Args:
            evaluation_data: List of (similarity_score, is_relevant) tuples
            target_precision: Target precision level (default 0.9)
        
        Returns:
            Optimal threshold value
        """
        if not evaluation_data:
            return 0.7
        
        evaluation_data.sort(key=lambda x: x[0], reverse=True)
        
        best_threshold = 0.7
        best_f1 = 0.0
        
        for i, (score, _) in enumerate(evaluation_data):
            threshold = score
            tp = sum(1 for s, rel in evaluation_data if s >= threshold and rel)
            fp = sum(1 for s, rel in evaluation_data if s >= threshold and not rel)
            fn = sum(1 for s, rel in evaluation_data if s < threshold and rel)
            
            if tp + fp == 0:
                continue
            
            precision = tp / (tp + fp)
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            
            if precision >= target_precision:
                f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
                if f1 > best_f1:
                    best_f1 = f1
                    best_threshold = threshold
        
        return best_threshold
    
    def calibrate_escalation_threshold(self,
                                      historical_updates: List[Dict],
                                      target_escalation_rate: float = 0.08) -> float:
        """
        Calibrate escalation threshold based on historical belief updates
        
        Args:
            historical_updates: List of belief update records with delta and outcomes
            target_escalation_rate: Target percentage of updates to escalate (default 8%)
        
        Returns:
            Optimal delta threshold for escalation
        """
        if not historical_updates:
            return 0.5
        
        deltas = [abs(update.get('log_odds_delta', 0)) for update in historical_updates]
        deltas.sort(reverse=True)
        
        target_count = int(len(deltas) * target_escalation_rate)
        if target_count == 0 or target_count >= len(deltas):
            return 0.5
        
        return deltas[target_count]
    
    def compute_brier_score(self, predictions: List[Tuple[float, bool]]) -> float:
        """
        Compute Brier score for belief calibration
        
        Args:
            predictions: List of (predicted_probability, actual_outcome) tuples
        
        Returns:
            Brier score (lower is better, 0 is perfect)
        """
        if not predictions:
            return 1.0
        
        squared_errors = [(p - (1.0 if o else 0.0)) ** 2 for p, o in predictions]
        return sum(squared_errors) / len(squared_errors)
    
    def analyze_calibration_curve(self, 
                                  predictions: List[Tuple[float, bool]],
                                  n_bins: int = 10) -> Dict[str, List[float]]:
        """
        Analyze calibration curve by binning predictions
        
        Args:
            predictions: List of (predicted_probability, actual_outcome) tuples
            n_bins: Number of bins for calibration curve
        
        Returns:
            Dictionary with bin_centers, observed_frequencies, and counts
        """
        if not predictions:
            return {"bin_centers": [], "observed_frequencies": [], "counts": []}
        
        bins = np.linspace(0, 1, n_bins + 1)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        
        binned_data = [[] for _ in range(n_bins)]
        for pred, outcome in predictions:
            bin_idx = min(int(pred * n_bins), n_bins - 1)
            binned_data[bin_idx].append(outcome)
        
        observed_frequencies = []
        counts = []
        for bin_data in binned_data:
            if bin_data:
                observed_frequencies.append(sum(bin_data) / len(bin_data))
                counts.append(len(bin_data))
            else:
                observed_frequencies.append(0.0)
                counts.append(0)
        
        return {
            "bin_centers": bin_centers.tolist(),
            "observed_frequencies": observed_frequencies,
            "counts": counts
        }
    
    def get_optimal_thresholds_from_db(self) -> Dict[str, float]:
        """
        Compute optimal thresholds based on historical data in database
        
        Returns:
            Dictionary with recommended thresholds
        """
        query = """
            SELECT log_odds_delta, uncertainty
            FROM belief_updates
            WHERE created_at >= NOW() - INTERVAL '90 days'
            ORDER BY created_at DESC
            LIMIT 1000
        """
        results = self.store.fetch_all(query)
        
        if not results:
            return {
                "relevance_threshold": 0.7,
                "escalation_delta_threshold": 0.5,
                "escalation_uncertainty_threshold": 0.4
            }
        
        deltas = [abs(row[0]) for row in results if row[0] is not None]
        uncertainties = [row[1] for row in results if row[1] is not None]
        
        if deltas:
            deltas_sorted = sorted(deltas, reverse=True)
            escalation_delta = deltas_sorted[int(len(deltas_sorted) * 0.08)]
        else:
            escalation_delta = 0.5
        
        if uncertainties:
            uncertainties_sorted = sorted(uncertainties, reverse=True)
            escalation_uncertainty = uncertainties_sorted[int(len(uncertainties_sorted) * 0.10)]
        else:
            escalation_uncertainty = 0.4
        
        return {
            "relevance_threshold": 0.7,
            "escalation_delta_threshold": max(0.3, min(0.7, escalation_delta)),
            "escalation_uncertainty_threshold": max(0.3, min(0.5, escalation_uncertainty))
        }
