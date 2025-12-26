import pytest
from edge.m5_observability.receipts.m1_linkage import add_m1_linkage


def test_add_m1_linkage_to_empty_receipt():
    """Test adding M1 linkage to an empty receipt."""
    receipt = {}
    coverage = 0.72
    roi_tags = ["triage_readiness", "observability_gain"]
    
    result = add_m1_linkage(receipt, coverage, roi_tags)
    
    # Verify inputs exists and has telemetry_coverage_pct
    assert "inputs" in result
    assert result["inputs"]["telemetry_coverage_pct"] == 0.72
    
    # Verify roi_tags
    assert result["roi_tags"] == ["triage_readiness", "observability_gain"]


def test_add_m1_linkage_preserves_existing_inputs():
    """Test that adding M1 linkage preserves other inputs."""
    receipt = {
        "inputs": {
            "existing_field": "value",
            "another_field": 123
        }
    }
    coverage = 0.85
    roi_tags = ["high_value"]
    
    result = add_m1_linkage(receipt, coverage, roi_tags)
    
    # Original inputs preserved
    assert result["inputs"]["existing_field"] == "value"
    assert result["inputs"]["another_field"] == 123
    
    # New field added
    assert result["inputs"]["telemetry_coverage_pct"] == 0.85
    assert result["roi_tags"] == ["high_value"]


def test_add_m1_linkage_preserves_other_receipt_fields():
    """Test that other receipt fields are preserved."""
    receipt = {
        "module": "M5_observability_v1",
        "gate_id": "test_gate",
        "timestamp": 12345
    }
    coverage = 0.90
    roi_tags = ["critical", "security"]
    
    result = add_m1_linkage(receipt, coverage, roi_tags)
    
    # Original fields preserved
    assert result["module"] == "M5_observability_v1"
    assert result["gate_id"] == "test_gate"
    assert result["timestamp"] == 12345
    
    # New fields added
    assert result["inputs"]["telemetry_coverage_pct"] == 0.90
    assert result["roi_tags"] == ["critical", "security"]


def test_add_m1_linkage_with_various_coverage_values():
    """Test with different coverage values."""
    test_cases = [
        (0.0, ["tag1"]),
        (0.5, ["tag2"]),
        (1.0, ["tag3"]),
        (0.333, ["tag4", "tag5"]),
    ]
    
    for coverage, tags in test_cases:
        receipt = {}
        result = add_m1_linkage(receipt, coverage, tags)
        
        assert result["inputs"]["telemetry_coverage_pct"] == coverage
        assert result["roi_tags"] == tags


def test_add_m1_linkage_with_empty_roi_tags():
    """Test with empty ROI tags list."""
    receipt = {}
    coverage = 0.5
    roi_tags = []
    
    result = add_m1_linkage(receipt, coverage, roi_tags)
    
    assert result["inputs"]["telemetry_coverage_pct"] == 0.5
    assert result["roi_tags"] == []


def test_add_m1_linkage_overwrites_existing_roi_tags():
    """Test that ROI tags are overwritten if they exist."""
    receipt = {
        "roi_tags": ["old_tag1", "old_tag2"]
    }
    coverage = 0.75
    roi_tags = ["new_tag1", "new_tag2", "new_tag3"]
    
    result = add_m1_linkage(receipt, coverage, roi_tags)
    
    assert result["roi_tags"] == ["new_tag1", "new_tag2", "new_tag3"]
    assert result["inputs"]["telemetry_coverage_pct"] == 0.75


def test_add_m1_linkage_overwrites_existing_coverage():
    """Test that coverage is overwritten if it exists."""
    receipt = {
        "inputs": {
            "telemetry_coverage_pct": 0.1
        }
    }
    coverage = 0.99
    roi_tags = ["updated"]
    
    result = add_m1_linkage(receipt, coverage, roi_tags)
    
    assert result["inputs"]["telemetry_coverage_pct"] == 0.99
    assert result["roi_tags"] == ["updated"]


def test_deterministic_behavior():
    """Test that same inputs produce same outputs."""
    receipt1 = {}
    receipt2 = {}
    coverage = 0.72
    roi_tags = ["triage_readiness", "observability_gain"]
    
    result1 = add_m1_linkage(receipt1, coverage, roi_tags)
    result2 = add_m1_linkage(receipt2, coverage, roi_tags)
    
    assert result1["inputs"]["telemetry_coverage_pct"] == result2["inputs"]["telemetry_coverage_pct"]
    assert result1["roi_tags"] == result2["roi_tags"]


def test_multiple_roi_tags():
    """Test with multiple ROI tags."""
    receipt = {}
    coverage = 0.88
    roi_tags = [
        "triage_readiness",
        "observability_gain",
        "security_posture",
        "compliance_ready"
    ]
    
    result = add_m1_linkage(receipt, coverage, roi_tags)
    
    assert result["inputs"]["telemetry_coverage_pct"] == 0.88
    assert result["roi_tags"] == roi_tags
    assert len(result["roi_tags"]) == 4

