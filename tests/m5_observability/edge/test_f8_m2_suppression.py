import pytest
from edge.m5_observability.integrations.m2_suppression import (
    apply_m2_conflict_hot_suppression,
    apply_suppression_to_receipt
)


def test_m2_warn_with_overlap():
    """Test that M2 WARN + overlap triggers explain_only mode."""
    files_touched = ["src/api/routes.py", "src/handlers.py"]
    m2_outcome = "warn"
    m2_conflict_files = ["src/api/routes.py", "config.yaml"]
    
    result = apply_m2_conflict_hot_suppression(
        files_touched, m2_outcome, m2_conflict_files
    )
    
    assert result["execution_mode"] == "explain_only"
    assert result["writes_allowed"] is False
    assert result["suppressed"] is True


def test_m2_soft_block_with_overlap():
    """Test that M2 soft_block + overlap triggers explain_only mode."""
    files_touched = ["lib/utils.js"]
    m2_outcome = "soft_block"
    m2_conflict_files = ["lib/utils.js"]
    
    result = apply_m2_conflict_hot_suppression(
        files_touched, m2_outcome, m2_conflict_files
    )
    
    assert result["execution_mode"] == "explain_only"
    assert result["writes_allowed"] is False
    assert result["suppressed"] is True


def test_m2_hard_block_with_overlap():
    """Test that M2 hard_block + overlap triggers explain_only mode."""
    files_touched = ["app.ts"]
    m2_outcome = "hard_block"
    m2_conflict_files = ["app.ts"]
    
    result = apply_m2_conflict_hot_suppression(
        files_touched, m2_outcome, m2_conflict_files
    )
    
    assert result["execution_mode"] == "explain_only"
    assert result["writes_allowed"] is False
    assert result["suppressed"] is True


def test_m2_pass_no_suppression():
    """Test that M2 pass outcome does not trigger suppression."""
    files_touched = ["src/api/routes.py"]
    m2_outcome = "pass"
    m2_conflict_files = ["src/api/routes.py"]
    
    result = apply_m2_conflict_hot_suppression(
        files_touched, m2_outcome, m2_conflict_files
    )
    
    assert result["execution_mode"] == "normal"
    assert result["writes_allowed"] is True
    assert result["suppressed"] is False


def test_no_overlap_no_suppression():
    """Test that no overlap means no suppression even with hot outcome."""
    files_touched = ["src/api/routes.py"]
    m2_outcome = "warn"
    m2_conflict_files = ["src/handlers.py", "config.yaml"]
    
    result = apply_m2_conflict_hot_suppression(
        files_touched, m2_outcome, m2_conflict_files
    )
    
    assert result["execution_mode"] == "normal"
    assert result["writes_allowed"] is True
    assert result["suppressed"] is False


def test_path_normalization():
    """Test that path normalization handles case and backslashes."""
    files_touched = ["Src\\API\\Routes.py"]
    m2_outcome = "warn"
    m2_conflict_files = ["src/api/routes.py"]
    
    result = apply_m2_conflict_hot_suppression(
        files_touched, m2_outcome, m2_conflict_files
    )
    
    # Should detect overlap due to normalization
    assert result["execution_mode"] == "explain_only"
    assert result["writes_allowed"] is False
    assert result["suppressed"] is True


def test_apply_suppression_to_receipt():
    """Test that suppression is correctly applied to receipt."""
    receipt = {
        "module": "M5_observability_v1",
        "gate_id": "test_gate"
    }
    
    suppression = {
        "execution_mode": "explain_only",
        "writes_allowed": False,
        "suppressed": True
    }
    
    result = apply_suppression_to_receipt(receipt, suppression)
    
    assert result["execution_mode"] == "explain_only"
    assert "actions" in result
    assert result["actions"]["writes_allowed"] is False


def test_apply_suppression_preserves_existing_receipt_fields():
    """Test that applying suppression preserves other receipt fields."""
    receipt = {
        "module": "M5_observability_v1",
        "gate_id": "test_gate",
        "timestamp": 12345,
        "actions": {
            "other_action": "value"
        }
    }
    
    suppression = {
        "execution_mode": "normal",
        "writes_allowed": True,
        "suppressed": False
    }
    
    result = apply_suppression_to_receipt(receipt, suppression)
    
    # Original fields preserved
    assert result["module"] == "M5_observability_v1"
    assert result["gate_id"] == "test_gate"
    assert result["timestamp"] == 12345
    
    # New fields added/updated
    assert result["execution_mode"] == "normal"
    assert result["actions"]["writes_allowed"] is True
    
    # Existing actions preserved
    assert result["actions"]["other_action"] == "value"


def test_deterministic_behavior():
    """Test that same inputs produce same outputs."""
    files_touched = ["file.py"]
    m2_outcome = "warn"
    m2_conflict_files = ["file.py"]
    
    result1 = apply_m2_conflict_hot_suppression(
        files_touched, m2_outcome, m2_conflict_files
    )
    result2 = apply_m2_conflict_hot_suppression(
        files_touched, m2_outcome, m2_conflict_files
    )
    
    assert result1 == result2


def test_empty_lists():
    """Test behavior with empty file lists."""
    # No files touched
    result1 = apply_m2_conflict_hot_suppression([], "warn", ["file.py"])
    assert result1["execution_mode"] == "normal"
    assert result1["suppressed"] is False
    
    # No conflict files
    result2 = apply_m2_conflict_hot_suppression(["file.py"], "warn", [])
    assert result2["execution_mode"] == "normal"
    assert result2["suppressed"] is False
    
    # Both empty
    result3 = apply_m2_conflict_hot_suppression([], "warn", [])
    assert result3["execution_mode"] == "normal"
    assert result3["suppressed"] is False

