import pytest
from edge.m5_observability.checks.pii_detector import detect_pii


def test_pii_detection():
    """Test PII detection with 3 patterns in diff."""
    unified_diff = """--- a/src/handlers/orders.ts
+++ b/src/handlers/orders.ts
@@ -5,3 +5,6 @@
 existing code
+Authorization: Bearer abc
+email=test@example.com
+token=abcd
 existing code
"""
    
    rules = [
        {"rule_id": "PII-001", "pattern": r"Bearer\s+\w+"},
        {"rule_id": "PII-002", "pattern": r"email=[^\s]+"},
        {"rule_id": "PII-003", "pattern": r"token=\w+"}
    ]
    
    result = detect_pii(unified_diff, rules)
    
    # Assert 3 findings exist
    assert len(result) == 3
    
    # Check each finding has correct structure
    for finding in result:
        assert "rule_id" in finding
        assert "file" in finding
        assert "line" in finding
        assert "match" in finding
    
    # Check file is correct
    assert all(f["file"] == "src/handlers/orders.ts" for f in result)
    
    # Check rule_ids
    rule_ids = [f["rule_id"] for f in result]
    assert "PII-001" in rule_ids
    assert "PII-002" in rule_ids
    assert "PII-003" in rule_ids
    
    # Check matches
    matches = [f["match"] for f in result]
    assert "Bearer abc" in matches
    assert "email=test@example.com" in matches
    assert "token=abcd" in matches
    
    # Check line numbers (hunk starts at +5, first added line is 5)
    # Line 5: Authorization: Bearer abc
    # Line 6: email=test@example.com
    # Line 7: token=abcd
    lines = [f["line"] for f in result]
    assert 5 in lines
    assert 6 in lines
    assert 7 in lines
    
    # Check ordering is deterministic (sorted)
    assert result == sorted(result, key=lambda x: (x["file"], x["line"], x["rule_id"], x["match"]))


def test_determinism():
    """Test that calling detect_pii twice returns identical list."""
    unified_diff = """--- a/src/handlers/orders.ts
+++ b/src/handlers/orders.ts
@@ -5,3 +5,6 @@
 existing code
+Authorization: Bearer abc
+email=test@example.com
+token=abcd
 existing code
"""
    
    rules = [
        {"rule_id": "PII-001", "pattern": r"Bearer\s+\w+"},
        {"rule_id": "PII-002", "pattern": r"email=[^\s]+"},
        {"rule_id": "PII-003", "pattern": r"token=\w+"}
    ]
    
    result1 = detect_pii(unified_diff, rules)
    result2 = detect_pii(unified_diff, rules)
    
    assert result1 == result2
    assert len(result1) == len(result2)
    for i in range(len(result1)):
        assert result1[i] == result2[i]

