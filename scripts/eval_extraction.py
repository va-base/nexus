"""Evaluate extraction quality"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from nexus.extraction.mock_extractor import MockExtractor


def eval_extraction():
    """Evaluate extraction quality"""
    print("Evaluating extraction quality...")
    
    extractor = MockExtractor()
    
    test_cases = [
        {
            "text": "Revenue of $150 million grew 35% year over year",
            "expected_types": ["financial"],
            "expected_count": 2  # revenue + growth
        },
        {
            "text": "We are hiring 50 new engineers and see strong demand",
            "expected_types": ["operational", "sentiment"],
            "expected_count": 2
        },
        {
            "text": "Gross margin expanded to 75% from 70% last quarter",
            "expected_types": ["financial"],
            "expected_count": 1
        }
    ]
    
    total_tests = len(test_cases)
    passed_tests = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest case {i}: {test_case['text'][:50]}...")
        
        claims = extractor.extract_claims(test_case["text"])
        
        if len(claims) >= test_case["expected_count"]:
            print(f"  ✓ Extracted {len(claims)} claims (expected >= {test_case['expected_count']})")
        else:
            print(f"  ✗ Extracted {len(claims)} claims (expected >= {test_case['expected_count']})")
            continue
        
        claim_types = set(c["claim_type"] for c in claims)
        expected_types = set(test_case["expected_types"])
        
        if expected_types.issubset(claim_types):
            print(f"  ✓ Found expected types: {expected_types}")
            passed_tests += 1
        else:
            print(f"  ✗ Missing types. Found: {claim_types}, Expected: {expected_types}")
    
    precision = passed_tests / total_tests if total_tests > 0 else 0
    
    print(f"\n{'='*60}")
    print(f"Evaluation Results:")
    print(f"  Tests passed: {passed_tests}/{total_tests}")
    print(f"  Precision: {precision:.2%}")
    print(f"{'='*60}")
    
    print(f"\nTargets:")
    print(f"  Precision target: ≥90%")
    print(f"  Current: {precision:.2%}")
    
    if precision >= 0.9:
        print(f"  ✓ Target met!")
    else:
        print(f"  ✗ Below target")
    
    return precision >= 0.9


if __name__ == "__main__":
    success = eval_extraction()
    sys.exit(0 if success else 1)
