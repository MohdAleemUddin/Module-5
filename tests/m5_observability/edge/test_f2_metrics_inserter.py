import pytest
from unittest.mock import Mock
from edge.m5_observability.snippets.metrics_inserter import (
    validate_label_keys,
    plan_metrics_insert,
    apply_patch,
    apply_inverse
)


def test_happy_insert():
    """Test successful metrics snippet insertion with sorted labels."""
    original = "existing code\nmore code\n"
    policy_cfg = {
        "obs.sample_rate_default": 0.25,
        "obs.disallow_dynamic_keys": True
    }
    label_keys = ["status", "route"]
    marker = "metrics1"
    
    # Plan the insert
    plan = plan_metrics_insert("test.js", original, policy_cfg, label_keys, marker)
    
    # Verify patch is not blocked
    assert plan["patch"]["op"] == "insert_block"
    
    # Mock PC-1 check that allows the operation
    pc1_mock = Mock(return_value=True)
    
    # Apply patch
    result = apply_patch(original, plan["patch"], pc1_mock)
    
    # Verify snippet contains expected content
    assert "sample_rate=0.25" in result
    # Labels should be sorted: route, status
    assert "labels=[route,status]" in result
    assert "counter:<name>" in result
    assert "histogram:<name>" in result
    assert "timer:<name>" in result
    assert f"// <{marker}>" in result
    assert f"// </{marker}>" in result
    
    # Verify PC-1 was called once
    assert pc1_mock.call_count == 1


def test_idempotent_no_pc1_on_noop():
    """Test that second insert is noop and pc1 is not called."""
    original = "code\n"
    policy_cfg = {
        "obs.sample_rate_default": 0.5,
        "obs.disallow_dynamic_keys": True
    }
    label_keys = ["method", "path"]
    marker = "metrics2"
    
    # First insert
    plan1 = plan_metrics_insert("test.py", original, policy_cfg, label_keys, marker)
    pc1_mock1 = Mock(return_value=True)
    result1 = apply_patch(original, plan1["patch"], pc1_mock1)
    
    # Verify first insert called pc1
    assert pc1_mock1.call_count == 1
    
    # Second insert with same marker
    plan2 = plan_metrics_insert("test.py", result1, policy_cfg, label_keys, marker)
    
    # Verify both patches are noop
    assert plan2["patch"]["op"] == "noop"
    assert plan2["inverse_patch"]["op"] == "noop"
    
    # Apply noop patch
    pc1_mock2 = Mock(return_value=True)
    result2 = apply_patch(result1, plan2["patch"], pc1_mock2)
    
    # Verify unchanged
    assert result2 == result1
    
    # Verify pc1 was NOT called for noop
    assert pc1_mock2.call_count == 0


def test_dynamic_key_blocked():
    """Test that dynamic keys are blocked and pc1 is not called."""
    original = "code\n"
    policy_cfg = {
        "obs.sample_rate_default": 0.1,
        "obs.disallow_dynamic_keys": True
    }
    label_keys = ["user.${id}", "normal_key"]
    marker = "metrics3"
    
    # Plan the insert
    plan = plan_metrics_insert("test.js", original, policy_cfg, label_keys, marker)
    
    # Verify patch is blocked
    assert plan["patch"]["op"] == "blocked"
    assert "user.${id}" in plan["patch"]["reason"]
    assert plan["inverse_patch"]["op"] == "noop"
    
    # Try to apply - should raise ValueError
    pc1_mock = Mock(return_value=True)
    
    with pytest.raises(ValueError) as exc_info:
        apply_patch(original, plan["patch"], pc1_mock)
    
    # Verify reason is in error message
    assert "user.${id}" in str(exc_info.value)
    
    # Verify pc1 was NOT called for blocked operation
    assert pc1_mock.call_count == 0


@pytest.mark.parametrize("newline_style", ["\n", "\r\n"])
def test_inverse_restores_original(newline_style):
    """Test that inverse patch restores original text exactly."""
    original = f"line1{newline_style}line2{newline_style}line3{newline_style}"
    policy_cfg = {
        "obs.sample_rate_default": 0.75,
        "obs.disallow_dynamic_keys": True
    }
    label_keys = ["endpoint", "method"]
    marker = "metrics4"
    
    # Insert snippet
    plan = plan_metrics_insert("test.js", original, policy_cfg, label_keys, marker)
    pc1_insert = Mock(return_value=True)
    modified = apply_patch(original, plan["patch"], pc1_insert)
    
    # Verify modified is different
    assert modified != original
    
    # Verify correct newline style was used
    if newline_style == "\r\n":
        assert "\r\n" in modified
    
    # Apply inverse
    pc1_remove = Mock(return_value=True)
    restored = apply_inverse(modified, plan["inverse_patch"], pc1_remove)
    
    # Verify restored equals original exactly
    assert restored == original
    
    # Verify pc1 was called for both operations
    assert pc1_insert.call_count == 1
    assert pc1_remove.call_count == 1


def test_pc1_enforced_insert():
    """Test that PC-1 denial on insert raises PermissionError."""
    original = "content\n"
    policy_cfg = {
        "obs.sample_rate_default": 0.9,
        "obs.disallow_dynamic_keys": False
    }
    label_keys = ["type"]
    marker = "metrics5"
    
    plan = plan_metrics_insert("test.py", original, policy_cfg, label_keys, marker)
    
    # PC-1 denies the operation
    pc1_mock = Mock(return_value=False)
    
    # Should raise PermissionError
    with pytest.raises(PermissionError):
        apply_patch(original, plan["patch"], pc1_mock)
    
    # Verify pc1 was called
    assert pc1_mock.call_count == 1


def test_pc1_enforced_remove():
    """Test that PC-1 denial on remove raises PermissionError."""
    original = "code\n"
    policy_cfg = {
        "obs.sample_rate_default": 0.33,
        "obs.disallow_dynamic_keys": True
    }
    label_keys = ["operation"]
    marker = "metrics6"
    
    # First insert with permission
    plan = plan_metrics_insert("test.js", original, policy_cfg, label_keys, marker)
    pc1_insert = Mock(return_value=True)
    modified = apply_patch(original, plan["patch"], pc1_insert)
    
    # Try to remove without permission
    pc1_remove = Mock(return_value=False)
    
    with pytest.raises(PermissionError):
        apply_inverse(modified, plan["inverse_patch"], pc1_remove)
    
    # Verify pc1 was called
    assert pc1_remove.call_count == 1


def test_validate_label_keys_invalid_chars():
    """Test that validate_label_keys detects unsafe characters."""
    # Test various unsafe patterns
    is_valid, invalid = validate_label_keys(["user.${id}"], True)
    assert not is_valid
    assert "user.${id}" in invalid
    
    is_valid, invalid = validate_label_keys(["key[0]"], True)
    assert not is_valid
    assert "key[0]" in invalid
    
    is_valid, invalid = validate_label_keys(["func()"], True)
    assert not is_valid
    assert "func()" in invalid
    
    is_valid, invalid = validate_label_keys(["has space"], True)
    assert not is_valid
    assert "has space" in invalid
    
    is_valid, invalid = validate_label_keys(["has:colon"], True)
    assert not is_valid
    assert "has:colon" in invalid


def test_validate_label_keys_allow_when_disabled():
    """Test that validation passes when disallow_dynamic_keys is False."""
    is_valid, invalid = validate_label_keys(["user.${id}"], False)
    assert is_valid
    assert invalid == []


def test_missing_policy_keys():
    """Test that missing policy keys raise ValueError."""
    original = "code\n"
    incomplete_cfg = {"obs.sample_rate_default": 0.5}
    
    with pytest.raises(ValueError) as exc_info:
        plan_metrics_insert("test.js", original, incomplete_cfg, ["key"], "m1")
    
    assert "obs.disallow_dynamic_keys" in str(exc_info.value)


def test_label_keys_normalization():
    """Test that label keys are deduplicated and sorted."""
    original = "code\n"
    policy_cfg = {
        "obs.sample_rate_default": 0.5,
        "obs.disallow_dynamic_keys": True
    }
    # Provide duplicates and unsorted
    label_keys = ["zebra", "apple", "zebra", "banana"]
    marker = "metrics7"
    
    plan = plan_metrics_insert("test.js", original, policy_cfg, label_keys, marker)
    pc1_mock = Mock(return_value=True)
    result = apply_patch(original, plan["patch"], pc1_mock)
    
    # Should be sorted unique: apple, banana, zebra
    assert "labels=[apple,banana,zebra]" in result

