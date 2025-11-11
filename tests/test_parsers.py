"""Test parsers"""
import pytest
from nexus.ingestion.parsers import FilingParser, TranscriptParser, JobPostingParser


def test_filing_parser():
    """Test filing parser"""
    parser = FilingParser()
    content = "<html><body>Revenue of $150 million</body></html>"
    result = parser.parse(content, {"filing_type": "10-Q"})
    
    assert "sections" in result
    assert "financials" in result


def test_transcript_parser():
    """Test transcript parser"""
    parser = TranscriptParser()
    content = "Revenue was $150 million. EPS was $1.50."
    result = parser.parse(content, {})
    
    assert "metrics" in result
    assert "guidance" in result


def test_job_posting_parser():
    """Test job posting parser"""
    parser = JobPostingParser()
    content = "Senior Software Engineer\nEngineering team"
    result = parser.parse(content, {"title": "Senior Software Engineer"})
    
    assert result["seniority"] == "senior"
    assert "keywords" in result
