"""Document parsers for various source types"""
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup


class FilingParser:
    """Parse SEC filings (10-Q, 10-K, 8-K)"""
    
    def parse(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse filing content"""
        soup = BeautifulSoup(content, 'html.parser')
        
        sections = self._extract_sections(soup)
        
        financials = self._extract_financials(soup)
        
        return {
            "sections": sections,
            "financials": financials,
            "filing_type": metadata.get("filing_type", "10-Q"),
            "parsed_at": datetime.utcnow().isoformat()
        }
    
    def _extract_sections(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract key sections from filing"""
        sections = {}
        
        section_patterns = {
            "risk_factors": r"risk\s+factors",
            "mda": r"management'?s?\s+discussion",
            "financial_statements": r"financial\s+statements"
        }
        
        for section_name, pattern in section_patterns.items():
            header = soup.find(string=re.compile(pattern, re.IGNORECASE))
            if header:
                parent = header.find_parent()
                if parent:
                    sections[section_name] = parent.get_text(strip=True)[:5000]
        
        return sections
    
    def _extract_financials(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract financial metrics"""
        text = soup.get_text()
        
        financials = {}
        
        revenue_match = re.search(r'revenue[s]?\s+of\s+\$?([\d,]+)\s*million', text, re.IGNORECASE)
        if revenue_match:
            financials["revenue_millions"] = float(revenue_match.group(1).replace(',', ''))
        
        growth_match = re.search(r'([\d.]+)%\s+(?:increase|growth|yoy)', text, re.IGNORECASE)
        if growth_match:
            financials["growth_rate"] = float(growth_match.group(1)) / 100
        
        return financials


class TranscriptParser:
    """Parse earnings call transcripts"""
    
    def parse(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse transcript content"""
        sections = self._split_sections(content)
        
        prepared_remarks = self._extract_statements(sections.get("prepared_remarks", ""))
        qa_section = self._extract_statements(sections.get("qa", ""))
        
        metrics = self._extract_metrics(content)
        
        guidance = self._extract_guidance(content)
        
        return {
            "prepared_remarks": prepared_remarks,
            "qa": qa_section,
            "metrics": metrics,
            "guidance": guidance,
            "parsed_at": datetime.utcnow().isoformat()
        }
    
    def _split_sections(self, content: str) -> Dict[str, str]:
        """Split transcript into sections"""
        sections = {}
        
        qa_match = re.search(r'question[\s-]+and[\s-]+answer', content, re.IGNORECASE)
        if qa_match:
            sections["prepared_remarks"] = content[:qa_match.start()]
            sections["qa"] = content[qa_match.start():]
        else:
            sections["prepared_remarks"] = content
        
        return sections
    
    def _extract_statements(self, text: str) -> List[Dict[str, str]]:
        """Extract speaker statements"""
        statements = []
        
        speaker_pattern = r'([A-Z][a-z]+\s+[A-Z][a-z]+),\s+([^:]+):\s*'
        matches = re.finditer(speaker_pattern, text)
        
        positions = [(m.start(), m.end(), m.group(1), m.group(2)) for m in matches]
        
        for i, (start, end, name, title) in enumerate(positions):
            next_start = positions[i + 1][0] if i + 1 < len(positions) else len(text)
            statement_text = text[end:next_start].strip()
            
            if statement_text:
                statements.append({
                    "speaker": name,
                    "title": title,
                    "text": statement_text[:2000]
                })
        
        return statements
    
    def _extract_metrics(self, text: str) -> Dict[str, Any]:
        """Extract financial metrics"""
        metrics = {}
        
        revenue_match = re.search(r'revenue\s+(?:of|was)\s+\$?([\d.]+)\s*(billion|million)', text, re.IGNORECASE)
        if revenue_match:
            value = float(revenue_match.group(1))
            unit = revenue_match.group(2).lower()
            metrics["revenue"] = value * 1000 if unit == "billion" else value
        
        eps_match = re.search(r'earnings\s+per\s+share\s+(?:of|was)\s+\$?([\d.]+)', text, re.IGNORECASE)
        if eps_match:
            metrics["eps"] = float(eps_match.group(1))
        
        margin_match = re.search(r'(?:gross|operating)\s+margin\s+(?:of|was)\s+([\d.]+)%', text, re.IGNORECASE)
        if margin_match:
            metrics["margin"] = float(margin_match.group(1)) / 100
        
        return metrics
    
    def _extract_guidance(self, text: str) -> Dict[str, Any]:
        """Extract forward guidance"""
        guidance = {}
        
        guidance_match = re.search(r'guidance|outlook|expect', text, re.IGNORECASE)
        if guidance_match:
            guidance_text = text[guidance_match.start():guidance_match.start() + 1000]
            
            rev_guidance = re.search(r'revenue\s+(?:of|between)\s+\$?([\d.]+)(?:\s*to\s*\$?([\d.]+))?\s*(billion|million)', 
                                    guidance_text, re.IGNORECASE)
            if rev_guidance:
                low = float(rev_guidance.group(1))
                high = float(rev_guidance.group(2)) if rev_guidance.group(2) else low
                unit = rev_guidance.group(3).lower()
                multiplier = 1000 if unit == "billion" else 1
                guidance["revenue_low"] = low * multiplier
                guidance["revenue_high"] = high * multiplier
        
        return guidance


class JobPostingParser:
    """Parse job postings"""
    
    def parse(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse job posting"""
        title = metadata.get("title", self._extract_title(content))
        department = self._extract_department(content)
        seniority = self._extract_seniority(title)
        location = metadata.get("location", self._extract_location(content))
        keywords = self._extract_keywords(content)
        
        return {
            "title": title,
            "department": department,
            "seniority": seniority,
            "location": location,
            "keywords": keywords,
            "posting_date": metadata.get("posting_date"),
            "parsed_at": datetime.utcnow().isoformat()
        }
    
    def _extract_title(self, content: str) -> str:
        """Extract job title"""
        lines = content.split('\n')
        return lines[0].strip() if lines else "Unknown"
    
    def _extract_department(self, content: str) -> Optional[str]:
        """Extract department"""
        dept_patterns = [
            r'department:\s*([^\n]+)',
            r'team:\s*([^\n]+)',
        ]
        
        for pattern in dept_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        if re.search(r'engineer|developer|software', content, re.IGNORECASE):
            return "Engineering"
        elif re.search(r'sales|account|business development', content, re.IGNORECASE):
            return "Sales"
        elif re.search(r'marketing|growth', content, re.IGNORECASE):
            return "Marketing"
        
        return None
    
    def _extract_seniority(self, title: str) -> str:
        """Extract seniority level"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['vp', 'vice president', 'chief', 'head of']):
            return "executive"
        elif any(word in title_lower for word in ['director', 'principal']):
            return "director"
        elif any(word in title_lower for word in ['senior', 'sr', 'lead', 'staff']):
            return "senior"
        elif any(word in title_lower for word in ['junior', 'jr', 'associate']):
            return "junior"
        else:
            return "mid"
    
    def _extract_location(self, content: str) -> Optional[str]:
        """Extract location"""
        location_match = re.search(r'location:\s*([^\n]+)', content, re.IGNORECASE)
        if location_match:
            return location_match.group(1).strip()
        
        if re.search(r'remote', content, re.IGNORECASE):
            return "Remote"
        
        return None
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract relevant keywords"""
        keywords = []
        
        keyword_patterns = {
            "ai": r'\b(?:ai|artificial intelligence|machine learning|ml|deep learning)\b',
            "cloud": r'\b(?:cloud|aws|azure|gcp)\b',
            "data": r'\b(?:data|analytics|big data)\b',
            "blockchain": r'\b(?:blockchain|crypto|web3)\b',
            "mobile": r'\b(?:mobile|ios|android)\b',
        }
        
        content_lower = content.lower()
        for keyword, pattern in keyword_patterns.items():
            if re.search(pattern, content_lower, re.IGNORECASE):
                keywords.append(keyword)
        
        return keywords
