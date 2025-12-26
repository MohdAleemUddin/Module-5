import pytest
from unittest.mock import Mock
from edge.m5_observability.snippets.correlation_injector import (
    has_correlation_helper,
    plan_correlation_inject,
    apply_patch,
    apply_inverse
)


def test_policy_off_noop():
    """Test that when policy is off, no injection occurs and pc1 not called."""
    original = "existing code\nmore code\n"
    policy_cfg = {"obs.require_correlation_id": False}
    marker = "corr1"
    
    # Plan the injection
    plan = plan_correlation_inject("test.js", original, policy_cfg, marker)
    
    # Verify patch is noop
    assert plan["patch"]["op"] == "noop"
    assert plan["inverse_patch"]["op"] == "noop"
    
    # Apply noop patch
    pc1_mock = Mock(return_value=True)
    result = apply_patch(original, plan["patch"], pc1_mock)
    
    # Verify unchanged
    assert result == original
    
    # Verify pc1 was NOT called for noop
    assert pc1_mock.call_count == 0


def test_already_present_helper_noop():
    """Test that if helper already exists, no duplicate is added and pc1 not called."""
    # Original text already has the required tokens
    original = """
existing code
function getCorrelationIds(ctx) {
  return {
    request_id: ctx.requestId,
    trace_id: ctx.traceId
  };
}
more code
"""
    policy_cfg = {"obs.require_correlation_id": True}
    marker = "corr2"
    
    # Verify detection works
    assert has_correlation_helper(original) is True
    
    # Plan the injection
    plan = plan_correlation_inject("test.js", original, policy_cfg, marker)
    
    # Verify patch is noop (helper already present)
    assert plan["patch"]["op"] == "noop"
    assert plan["inverse_patch"]["op"] == "noop"
    
    # Apply noop patch
    pc1_mock = Mock(return_value=True)
    result = apply_patch(original, plan["patch"], pc1_mock)
    
    # Verify unchanged
    assert result == original
    
    # Verify pc1 was NOT called
    assert pc1_mock.call_count == 0


def test_missing_helper_insert_once_idempotent():
    """Test that helper is inserted once and second run is noop (idempotent)."""
    original = "const app = express();\n"
    policy_cfg = {"obs.require_correlation_id": True}
    marker = "corr3"
    
    # First plan
    plan1 = plan_correlation_inject("test.js", original, policy_cfg, marker)
    
    # Verify patch is insert_block
    assert plan1["patch"]["op"] == "insert_block"
    assert plan1["inverse_patch"]["op"] == "remove_block"
    
    # Apply first patch
    pc1_mock1 = Mock(return_value=True)
    result1 = apply_patch(original, plan1["patch"], pc1_mock1)
    
    # Verify insertion occurred
    assert result1 != original
    assert "getCorrelationIds" in result1
    assert "request_id" in result1
    assert "trace_id" in result1
    assert f"// <{marker}>" in result1
    assert f"// </{marker}>" in result1
    
    # Verify pc1 was called once
    assert pc1_mock1.call_count == 1
    
    # Second plan on modified text
    plan2 = plan_correlation_inject("test.js", result1, policy_cfg, marker)
    
    # Verify second patch is noop (idempotent)
    assert plan2["patch"]["op"] == "noop"
    assert plan2["inverse_patch"]["op"] == "noop"
    
    # Apply noop patch
    pc1_mock2 = Mock(return_value=True)
    result2 = apply_patch(result1, plan2["patch"], pc1_mock2)
    
    # Verify unchanged
    assert result2 == result1
    
    # Verify pc1 was NOT called for noop
    assert pc1_mock2.call_count == 0


@pytest.mark.parametrize("newline_style", ["\n", "\r\n"])
def test_inverse_restores_original(newline_style):
    """Test that inverse patch restores original text exactly."""
    original = f"line1{newline_style}line2{newline_style}line3{newline_style}"
    policy_cfg = {"obs.require_correlation_id": True}
    marker = "corr4"
    
    # Insert helper
    plan = plan_correlation_inject("test.js", original, policy_cfg, marker)
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
    """Test that PC-1 denial on insert raises PermissionError and no change."""
    original = "content\n"
    policy_cfg = {"obs.require_correlation_id": True}
    marker = "corr5"
    
    plan = plan_correlation_inject("test.js", original, policy_cfg, marker)
    
    # PC-1 denies the operation
    pc1_mock = Mock(return_value=False)
    
    # Should raise PermissionError
    with pytest.raises(PermissionError):
        apply_patch(original, plan["patch"], pc1_mock)
    
    # Verify pc1 was called
    assert pc1_mock.call_count == 1


def test_pc1_enforced_remove():
    """Test that PC-1 denial on remove raises PermissionError and no change."""
    original = "code\n"
    policy_cfg = {"obs.require_correlation_id": True}
    marker = "corr6"
    
    # First insert with permission
    plan = plan_correlation_inject("test.js", original, policy_cfg, marker)
    pc1_insert = Mock(return_value=True)
    modified = apply_patch(original, plan["patch"], pc1_insert)
    
    # Try to remove without permission
    pc1_remove = Mock(return_value=False)
    
    with pytest.raises(PermissionError):
        apply_inverse(modified, plan["inverse_patch"], pc1_remove)
    
    # Verify pc1 was called
    assert pc1_remove.call_count == 1


def test_has_correlation_helper_detection():
    """Test that has_correlation_helper correctly detects required tokens."""
    # All tokens present
    text1 = "function getCorrelationIds() { return {request_id: 'x', trace_id: 'y'}; }"
    assert has_correlation_helper(text1) is True
    
    # Missing one token
    text2 = "function getCorrelationIds() { return {request_id: 'x'}; }"
    assert has_correlation_helper(text2) is False
    
    # Missing all tokens
    text3 = "const app = express();"
    assert has_correlation_helper(text3) is False
    
    # Tokens present but scattered
    text4 = """
    const request_id = getId();
    const trace_id = getTrace();
    function getCorrelationIds() { return {request_id, trace_id}; }
    """
    assert has_correlation_helper(text4) is True


def test_stub_contains_required_tokens():
    """Test that the injected stub contains all required tokens."""
    original = "code\n"
    policy_cfg = {"obs.require_correlation_id": True}
    marker = "corr7"
    
    plan = plan_correlation_inject("test.js", original, policy_cfg, marker)
    pc1_mock = Mock(return_value=True)
    result = apply_patch(original, plan["patch"], pc1_mock)
    
    # Verify all required tokens are present in result
    assert "request_id" in result
    assert "trace_id" in result
    assert "getCorrelationIds" in result

