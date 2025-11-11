"""Hiring Momentum investigation playbook"""
from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta
from collections import defaultdict
from nexus.investigation.playbooks import InvestigationPlaybook
from nexus.storage.feature_store import FeatureStore


class HiringMomentum(InvestigationPlaybook):
    """Hiring momentum investigation playbook"""
    
    def __init__(self, postgres_store=None, feature_store=None):
        super().__init__(postgres_store)
        self.feature_store = feature_store or FeatureStore(self.store)
    
    def get_playbook_name(self) -> str:
        return "hiring_momentum"
    
    def execute(self, investigation_id: UUID, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute hiring momentum investigation"""
        company_id = inputs.get("company_id")
        date_range = inputs.get("date_range", {})
        start_date = date_range.get("start_date", (datetime.utcnow() - timedelta(days=30)).date())
        end_date = date_range.get("end_date", datetime.utcnow().date())
        related_hypotheses = inputs.get("related_hypotheses", [])
        
        postings = self._aggregate_postings(company_id, start_date, end_date)
        
        velocity = self._compute_velocity(company_id, postings)
        
        departments = self._analyze_departments(postings)
        
        seniority = self._analyze_seniority(postings)
        
        themes = self._extract_themes(postings)
        
        benchmark = self._competitive_benchmark(company_id)
        
        memo_id = self._generate_memo(company_id, velocity, departments, seniority, themes, benchmark)
        
        belief_updates = self._update_beliefs(related_hypotheses, velocity)
        
        outputs = {
            "memo_id": str(memo_id),
            "hiring_velocity": velocity,
            "department_breakdown": departments,
            "seniority_mix": seniority,
            "theme_signals": themes,
            "competitive_benchmark": benchmark,
            "belief_updates": [str(u) for u in belief_updates],
            "completed_at": datetime.utcnow().isoformat()
        }
        
        self.update_investigation_status(investigation_id, "completed", outputs)
        
        return outputs
    
    def _aggregate_postings(self, company_id: UUID, start_date, end_date) -> List[Dict[str, Any]]:
        """Aggregate job postings in date range"""
        query = """
            SELECT id, source_date, title, raw_metadata
            FROM evidence
            WHERE company_id = :company_id
              AND source_type = 'hiring'
              AND source_date BETWEEN :start_date AND :end_date
            ORDER BY source_date DESC
        """
        results = self.store.fetch_all(query, {
            "company_id": str(company_id),
            "start_date": start_date,
            "end_date": end_date
        })
        
        postings = []
        for row in results:
            posting_id, source_date, title, raw_metadata = row
            postings.append({
                "id": posting_id,
                "date": source_date,
                "title": title,
                "metadata": raw_metadata or {}
            })
        
        return postings
    
    def _compute_velocity(self, company_id: UUID, postings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute hiring velocity metrics"""
        current_count = len(postings)
        
        query = """
            SELECT COUNT(*)
            FROM evidence
            WHERE company_id = :company_id
              AND source_type = 'hiring'
              AND source_date BETWEEN :start_date AND :end_date
        """
        
        baseline_end = datetime.utcnow().date() - timedelta(days=90)
        baseline_start = baseline_end - timedelta(days=30)
        result = self.store.fetch_one(query, {
            "company_id": str(company_id),
            "start_date": baseline_start,
            "end_date": baseline_end
        })
        baseline_count = result[0] if result else 1
        
        velocity_ratio = current_count / baseline_count if baseline_count > 0 else 1.0
        
        self.feature_store.write_feature(
            "company", company_id, "hiring_velocity_30d", float(current_count)
        )
        
        return {
            "current_30d": current_count,
            "baseline_30d": baseline_count,
            "velocity_ratio": velocity_ratio,
            "is_surge": velocity_ratio > 2.0
        }
    
    def _analyze_departments(self, postings: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze department breakdown"""
        departments = defaultdict(int)
        
        for posting in postings:
            dept = posting.get("metadata", {}).get("department", "Unknown")
            departments[dept] += 1
        
        return dict(departments)
    
    def _analyze_seniority(self, postings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze seniority mix"""
        seniority_counts = defaultdict(int)
        
        for posting in postings:
            seniority = posting.get("metadata", {}).get("seniority", "mid")
            seniority_counts[seniority] += 1
        
        total = len(postings)
        senior_count = seniority_counts.get("senior", 0) + seniority_counts.get("director", 0) + seniority_counts.get("executive", 0)
        senior_pct = (senior_count / total * 100) if total > 0 else 0
        
        return {
            "breakdown": dict(seniority_counts),
            "senior_count": senior_count,
            "senior_percentage": senior_pct,
            "indicates_expansion": senior_pct > 20
        }
    
    def _extract_themes(self, postings: List[Dict[str, Any]]) -> Dict[str, int]:
        """Extract hiring themes from keywords"""
        themes = defaultdict(int)
        
        for posting in postings:
            keywords = posting.get("metadata", {}).get("keywords", [])
            for keyword in keywords:
                themes[keyword] += 1
        
        return dict(themes)
    
    def _competitive_benchmark(self, company_id: UUID) -> Dict[str, Any]:
        """Benchmark against competitors"""
        query = "SELECT sector FROM companies WHERE id = :id"
        result = self.store.fetch_one(query, {"id": str(company_id)})
        
        if not result or not result[0]:
            return {}
        
        sector = result[0]
        
        query = """
            SELECT c.name, f.feature_value
            FROM features f
            JOIN companies c ON f.entity_id = c.id::text::uuid
            WHERE c.sector = :sector
              AND c.id != :company_id
              AND f.entity_type = 'company'
              AND f.feature_name = 'hiring_velocity_30d'
              AND f.computed_at >= NOW() - INTERVAL '7 days'
            ORDER BY f.feature_value DESC
            LIMIT 3
        """
        results = self.store.fetch_all(query, {"sector": sector, "company_id": str(company_id)})
        
        peers = [{"company": row[0], "velocity": row[1]} for row in results]
        
        return {
            "sector": sector,
            "peer_velocities": peers
        }
    
    def _generate_memo(self, company_id: UUID, velocity: Dict[str, Any],
                      departments: Dict[str, int], seniority: Dict[str, Any],
                      themes: Dict[str, int], benchmark: Dict[str, Any]) -> UUID:
        """Generate hiring momentum memo"""
        query = "SELECT name, ticker FROM companies WHERE id = :id"
        result = self.store.fetch_one(query, {"id": str(company_id)})
        company_name, ticker = result if result else ("Unknown", "N/A")
        
        content = f"""

- Current 30-day postings: {velocity['current_30d']}
- Baseline 30-day postings: {velocity['baseline_30d']}
- Velocity ratio: {velocity['velocity_ratio']:.2f}x
- Status: {'SURGE DETECTED' if velocity['is_surge'] else 'Normal'}

"""
        for dept, count in sorted(departments.items(), key=lambda x: x[1], reverse=True):
            content += f"- {dept}: {count} postings\n"
        
        content += f"\n## Seniority Mix\n"
        content += f"- Senior/Executive roles: {seniority['senior_count']} ({seniority['senior_percentage']:.1f}%)\n"
        content += f"- Indicates: {'Expansion' if seniority['indicates_expansion'] else 'Backfill'}\n"
        
        content += f"\n## Theme Signals\n"
        for theme, count in sorted(themes.items(), key=lambda x: x[1], reverse=True)[:5]:
            content += f"- {theme}: {count} postings\n"
        
        content += f"\n## Competitive Benchmark\n"
        content += f"Sector: {benchmark.get('sector', 'Unknown')}\n"
        for peer in benchmark.get('peer_velocities', []):
            content += f"- {peer['company']}: {peer['velocity']:.0f} postings/30d\n"
        
        query = """
            INSERT INTO memos (company_id, title, content, memo_type, author)
            VALUES (:company_id, :title, :content, :memo_type, :author)
            RETURNING id
        """
        result = self.store.execute(query, {
            "company_id": str(company_id),
            "title": f"Hiring Momentum: {ticker}",
            "content": content,
            "memo_type": "investigation",
            "author": "hiring_momentum_playbook"
        })
        
        return result.fetchone()[0]
    
    def _update_beliefs(self, hypothesis_ids: List[str], velocity: Dict[str, Any]) -> List[UUID]:
        """Update beliefs based on hiring signals"""
        updates = []
        
        if not velocity.get("is_surge"):
            return updates
        
        for hypothesis_id in hypothesis_ids:
            pass
        
        return updates
