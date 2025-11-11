"""MNPI (Material Non-Public Information) filter"""
import re
from typing import Dict, Any, List, Tuple


class MNPIFilter:
    """Filter for detecting MNPI in content"""
    
    MNPI_KEYWORDS = [
        "insider", "non-public", "confidential", "material non-public",
        "private placement", "unannounced", "undisclosed", "proprietary",
        "internal only", "restricted", "embargoed"
    ]
    
    MNPI_PATTERNS = [
        r'insider\s+(?:information|trading)',
        r'material\s+non-?public',
        r'confidential\s+(?:information|data)',
        r'unannounced\s+(?:merger|acquisition|deal)',
        r'private\s+placement',
        r'(?:before|prior to)\s+(?:public|official)\s+(?:announcement|release)',
    ]
    
    def check(self, content: str, metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Check if content contains MNPI, return (has_mnpi, flags)"""
        flags = []
        content_lower = content.lower()
        
        for keyword in self.MNPI_KEYWORDS:
            if keyword in content_lower:
                flags.append(f"MNPI keyword detected: {keyword}")
        
        for pattern in self.MNPI_PATTERNS:
            if re.search(pattern, content_lower, re.IGNORECASE):
                flags.append(f"MNPI pattern detected: {pattern}")
        
        if metadata.get("source_type") == "manual":
            earnings_pattern = r'(?:q[1-4]|quarter)\s+\d{4}\s+(?:revenue|earnings|eps).*?\$?[\d,]+(?:\.\d+)?'
            if re.search(earnings_pattern, content_lower, re.IGNORECASE):
                flags.append("Potential early earnings disclosure")
        
        return len(flags) > 0, flags
    
    def redact_pii(self, content: str) -> Tuple[str, Dict[str, List[str]]]:
        """Redact PII from content, return (redacted_content, redacted_fields)"""
        redacted_fields = {
            "emails": [],
            "phones": [],
            "ssns": []
        }
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, content)
        redacted_fields["emails"] = emails
        content = re.sub(email_pattern, '[EMAIL]', content)
        
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phones = re.findall(phone_pattern, content)
        redacted_fields["phones"] = phones
        content = re.sub(phone_pattern, '[PHONE]', content)
        
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        ssns = re.findall(ssn_pattern, content)
        redacted_fields["ssns"] = ssns
        content = re.sub(ssn_pattern, '[SSN]', content)
        
        return content, redacted_fields
