"""Evidence validation"""
from typing import Dict, Any, List
from datetime import datetime, date


class EvidenceValidator:
    """Validate evidence before processing"""
    
    def validate(self, evidence: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate evidence, return (is_valid, errors)"""
        errors = []
        
        if not evidence.get("content"):
            errors.append("Missing content")
        
        if not evidence.get("source_type"):
            errors.append("Missing source_type")
        
        valid_types = ["filing", "transcript", "news", "hiring", "manual"]
        if evidence.get("source_type") not in valid_types:
            errors.append(f"Invalid source_type: {evidence.get('source_type')}")
        
        if evidence.get("source_date"):
            try:
                source_date = evidence["source_date"]
                if isinstance(source_date, str):
                    source_date = datetime.fromisoformat(source_date).date()
                
                if source_date > date.today():
                    errors.append("Source date is in the future")
            except (ValueError, TypeError):
                errors.append("Invalid source_date format")
        
        content_size = len(evidence.get("content", ""))
        if content_size > 50 * 1024 * 1024:  # 50MB
            errors.append(f"Content too large: {content_size} bytes")
        
        if content_size < 100:
            errors.append(f"Content too small: {content_size} bytes")
        
        if not evidence.get("company_id") and not evidence.get("company"):
            errors.append("Missing company reference")
        
        return len(errors) == 0, errors
