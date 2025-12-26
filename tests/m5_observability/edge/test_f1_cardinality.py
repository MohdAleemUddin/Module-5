import pytest
from edge.m5_observability.checks.cardinality_detector import detect_cardinality


def test_dynamic_key():
    """Test dynamic key detection."""
    unified_diff = """--- a/src/handlers.py
+++ b/src/handlers.py
@@ -1,3 +1,4 @@
+labels[user.${id}] = 1
 existing code
"""
    
    result = detect_cardinality(unified_diff)
    
    assert "dynamic_key: labels[user.${id}]" in result
    assert len([x for x in result if x.startswith("dynamic_key:")]) == 1


def test_high_card_value():
    """Test high-cardinality value detection."""
    unified_diff = """--- a/src/handlers.py
+++ b/src/handlers.py
@@ -1,3 +1,4 @@
+labels['user_id'] = 'abcd1234efgh'
 existing code
"""
    
    result = detect_cardinality(unified_diff)
    
    # Should detect the id assignment with long value
    high_card_findings = [x for x in result if x.startswith("high_card_value:")]
    assert len(high_card_findings) >= 1
    # Check that the value is detected
    assert any("abcd1234efgh" in x for x in high_card_findings)


def test_safe_case():
    """Test that safe cases don't trigger findings."""
    unified_diff = """--- a/src/handlers.py
+++ b/src/handlers.py
@@ -1,3 +1,5 @@
+labels['env'] = 'prod'
+labels['route'] = '/health'
 existing code
"""
    
    result = detect_cardinality(unified_diff)
    
    # Should have no findings for safe static labels
    assert len(result) == 0


def test_determinism():
    """Test that calling detect_cardinality twice returns identical list."""
    unified_diff = """--- a/src/handlers.py
+++ b/src/handlers.py
@@ -1,3 +1,4 @@
+labels[user.${id}] = 1
+user_id = 'abcd1234efgh'
 existing code
"""
    
    result1 = detect_cardinality(unified_diff)
    result2 = detect_cardinality(unified_diff)
    
    assert result1 == result2
    assert len(result1) == len(result2)
    for i in range(len(result1)):
        assert result1[i] == result2[i]

