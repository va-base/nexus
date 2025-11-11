"""Earnings Deep Dive investigation playbook"""
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from nexus.investigation.playbooks import InvestigationPlaybook
from nexus.belief.engine import BeliefEngine


class EarningsDeepDive(InvestigationPlaybook):
    """Deep dive investigation for earnings events"""
    
    def __init__(self, postgres_store=None, belief_engine=None):
        super().__init__(postgres_store)
        self.belief_engine = belief_engine or BeliefEngine(self.store)
    
    def get_playbook_name(self) -> str:
        return "earnings_deep_dive"
    
    def execute(self, investigation_id: UUID, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute earnings deep dive investigation"""
        company_id = inputs.get("company_id")
        earnings_date = inputs.get("earnings_date")
        transcript_id = inputs.get("transcript_id")
        related_hypotheses = inputs.get("related_hypotheses", [])
        
        context = self._retrieve_context(company_id, earnings_date)
        
        metrics = self._extract_key_metrics(transcript_id) if transcript_id else {}
        
        deltas = self._compare_to_predictions(company_id, metrics, earnings_date)
        
        sentiment = self._analyze_sentiment(transcript_id) if transcript_id else {}
        
        competitive = self._get_competitive_context(company_id)
        
        memo_id = self._generate_memo(company_id, context, metrics, deltas, sentiment, competitive)
        
        belief_updates = self._update_beliefs(related_hypotheses, transcript_id)
        
        escalation_required = any(abs(u.get("delta", 0)) > 0.3 for u in belief_updates)
        
        outputs = {
            "memo_id": str(memo_id),
            "key_metrics": metrics,
            "prediction_deltas": deltas,
            "sentiment_scores": sentiment,
            "belief_updates": [str(u.get("update_id")) for u in belief_updates],
            "escalation_required": escalation_required,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        self.update_investigation_status(investigation_id, "completed", outputs)
        
        return outputs
    
    def _retrieve_context(self, company_id: UUID, earnings_date: str) -> Dict[str, Any]:
        """Retrieve company context"""
        query = "SELECT name, ticker, sector FROM companies WHERE id = :id"
        result = self.store.fetch_one(query, {"id": str(company_id)})
        
        if not result:
            return {}
        
        name, ticker, sector = result
        
        query = """
            SELECT feature_name, feature_value, computed_at
            FROM features
            WHERE entity_type = 'company' AND entity_id = :id
              AND feature_name IN ('revenue', 'eps', 'gross_margin', 'operating_margin')
              AND computed_at >= :since
            ORDER BY computed_at DESC
        """
        since = datetime.utcnow() - timedelta(days=365)
        financials = self.store.fetch_all(query, {"id": str(company_id), "since": since})
        
        return {
            "company_name": name,
            "ticker": ticker,
            "sector": sector,
            "recent_financials": [
                {"metric": row[0], "value": row[1], "date": row[2].isoformat()}
                for row in financials
            ]
        }
    
    def _extract_key_metrics(self, transcript_id: UUID) -> Dict[str, Any]:
        """Extract key metrics from transcript"""
        query = "SELECT content, raw_metadata FROM evidence WHERE id = :id"
        result = self.store.fetch_one(query, {"id": str(transcript_id)})
        
        if not result:
            return {}
        
        content, raw_metadata = result
        
        from nexus.ingestion.parsers import TranscriptParser
        parser = TranscriptParser()
        parsed = parser.parse(content, raw_metadata or {})
        
        return parsed.get("metrics", {})
    
    def _compare_to_predictions(self, company_id: UUID, metrics: Dict[str, Any], earnings_date: str) -> Dict[str, Any]:
        """Compare actual metrics to predictions"""
        deltas = {}
        
        for metric_name, actual_value in metrics.items():
            query = """
                SELECT predicted_value, confidence_lower, confidence_upper
                FROM predictions
                WHERE company_id = :company_id
                  AND metric_name = :metric_name
                  AND target_date <= :target_date
                ORDER BY prediction_date DESC
                LIMIT 1
            """
            result = self.store.fetch_one(query, {
                "company_id": str(company_id),
                "metric_name": metric_name,
                "target_date": earnings_date
            })
            
            if result:
                predicted, lower, upper = result
                delta = actual_value - predicted
                delta_pct = (delta / predicted * 100) if predicted != 0 else 0
                
                deltas[metric_name] = {
                    "predicted": predicted,
                    "actual": actual_value,
                    "delta": delta,
                    "delta_pct": delta_pct,
                    "miss": abs(delta_pct) > 5
                }
        
        return deltas
    
    def _analyze_sentiment(self, transcript_id: UUID) -> Dict[str, Any]:
        """Analyze sentiment from transcript"""
        query = """
            SELECT claim_type, polarity, magnitude, confidence
            FROM claims
            WHERE evidence_id = :evidence_id AND claim_type = 'sentiment'
        """
        results = self.store.fetch_all(query, {"evidence_id": str(transcript_id)})
        
        if not results:
            return {"overall": "neutral", "confidence": 0.5}
        
        positive_count = sum(1 for r in results if r[1] == "positive")
        negative_count = sum(1 for r in results if r[1] == "negative")
        avg_magnitude = sum(r[2] for r in results if r[2]) / len(results)
        avg_confidence = sum(r[3] for r in results if r[3]) / len(results)
        
        if positive_count > negative_count:
            overall = "positive"
        elif negative_count > positive_count:
            overall = "negative"
        else:
            overall = "neutral"
        
        return {
            "overall": overall,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "magnitude": avg_magnitude,
            "confidence": avg_confidence
        }
    
    def _get_competitive_context(self, company_id: UUID) -> Dict[str, Any]:
        """Get competitive context"""
        query = "SELECT sector FROM companies WHERE id = :id"
        result = self.store.fetch_one(query, {"id": str(company_id)})
        
        if not result or not result[0]:
            return {}
        
        sector = result[0]
        
        query = """
            SELECT c.name, cl.claim_text, cl.claim_type, cl.polarity
            FROM claims cl
            JOIN evidence e ON cl.evidence_id = e.id
            JOIN companies c ON e.company_id = c.id
            WHERE c.sector = :sector
              AND c.id != :company_id
              AND cl.created_at >= NOW() - INTERVAL '30 days'
            ORDER BY cl.created_at DESC
            LIMIT 10
        """
        results = self.store.fetch_all(query, {"sector": sector, "company_id": str(company_id)})
        
        return {
            "sector": sector,
            "competitor_signals": [
                {"company": row[0], "claim": row[1], "type": row[2], "polarity": row[3]}
                for row in results
            ]
        }
    
    def _generate_memo(self, company_id: UUID, context: Dict[str, Any], 
                      metrics: Dict[str, Any], deltas: Dict[str, Any],
                      sentiment: Dict[str, Any], competitive: Dict[str, Any]) -> UUID:
        """Generate investigation memo"""
        content = f"""

{context.get('company_name')} reported earnings with the following key takeaways:
- Overall sentiment: {sentiment.get('overall', 'neutral')}
- {len([d for d in deltas.values() if d.get('miss')])} metric(s) missed expectations

"""
        for metric, value in metrics.items():
            content += f"- {metric}: {value}\n"
        
        content += "\n## Prediction Deltas\n"
        for metric, delta_info in deltas.items():
            content += f"- {metric}: {delta_info.get('delta_pct', 0):.1f}% {'miss' if delta_info.get('miss') else 'in-line'}\n"
        
        content += f"\n## Sentiment Analysis\n"
        content += f"Overall: {sentiment.get('overall', 'neutral')} (confidence: {sentiment.get('confidence', 0):.2f})\n"
        
        content += f"\n## Competitive Context\n"
        content += f"Sector: {competitive.get('sector', 'Unknown')}\n"
        content += f"Recent competitor signals: {len(competitive.get('competitor_signals', []))}\n"
        
        import json
        query = """
            INSERT INTO memos (company_id, title, content, memo_type, author)
            VALUES (:company_id, :title, :content, :memo_type, :author)
            RETURNING id
        """
        result = self.store.execute(query, {
            "company_id": str(company_id),
            "title": f"Earnings Deep Dive: {context.get('ticker', 'N/A')}",
            "content": content,
            "memo_type": "investigation",
            "author": "earnings_deep_dive_playbook"
        })
        
        return result.fetchone()[0]
    
    def _update_beliefs(self, hypothesis_ids: List[str], transcript_id: UUID) -> List[Dict[str, Any]]:
        """Update beliefs for related hypotheses"""
        updates = []
        
        query = "SELECT id FROM claims WHERE evidence_id = :evidence_id"
        results = self.store.fetch_all(query, {"evidence_id": str(transcript_id)})
        claim_ids = [UUID(row[0]) for row in results]
        
        for hypothesis_id in hypothesis_ids:
            try:
                update = self.belief_engine.update_belief(
                    UUID(hypothesis_id),
                    claim_ids,
                    trigger_reason="earnings_investigation"
                )
                updates.append(update)
            except Exception as e:
                print(f"Error updating belief for {hypothesis_id}: {e}")
        
        return updates
