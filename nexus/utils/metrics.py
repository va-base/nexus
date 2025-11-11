"""Metrics collection utilities"""
from typing import Dict, Any
from datetime import datetime


class MetricsCollector:
    """Collect system metrics"""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {}
    
    def record_latency(self, operation: str, latency_ms: int):
        """Record operation latency"""
        if operation not in self.metrics:
            self.metrics[operation] = {"latencies": [], "count": 0}
        self.metrics[operation]["latencies"].append(latency_ms)
        self.metrics[operation]["count"] += 1
    
    def record_count(self, metric: str, value: int = 1):
        """Record a count metric"""
        if metric not in self.metrics:
            self.metrics[metric] = 0
        self.metrics[metric] += value
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        summary = {}
        for operation, data in self.metrics.items():
            if "latencies" in data:
                latencies = sorted(data["latencies"])
                n = len(latencies)
                summary[operation] = {
                    "count": data["count"],
                    "p50": latencies[n // 2] if n > 0 else 0,
                    "p95": latencies[int(n * 0.95)] if n > 0 else 0,
                    "p99": latencies[int(n * 0.99)] if n > 0 else 0
                }
            else:
                summary[operation] = data
        return summary
