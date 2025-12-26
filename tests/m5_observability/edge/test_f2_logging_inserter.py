import pytest
from unittest.mock import Mock
from edge.m5_observability.snippets.logging_inserter import (
    plan_logging_insert,
    apply_patch,
    apply_inverse
)


@pytest.mark.parametrize("newline_style", ["\n", "\r\n"])
def test_insert_once(newline_style):
    """Test that snippet is inserted once with correct newline style."""
    original = f"existing code{newline_style}more code{newline_style}"
    snippet = "console.log('test');"
    marker = "log1"
    
    # Plan the insert
    plan = plan_logging_insert("test.js", original, snippet, marker)
    
    # Mock PC-1 check that allows the operation
    pc1_mock = Mock(return_value=True)
    
    # Apply patch
    result = apply_patch(original, plan["patch"], pc1_mock)
    
    # Verify block appears exactly once
    assert f"// <{marker}>" in result
    assert f"// </{marker}>" in result
    assert snippet in result
    assert result.count(f"// <{marker}>") == 1
    assert result.count(f"// </{marker}>") == 1
    
    # Verify correct newline style
    if newline_style == "\r\n":
        assert "\r\n" in result
    
    # Verify PC-1 was called once
    assert pc1_mock.call_count == 1
    pc1_mock.assert_called_once_with(
        action="m5.log_snippet.insert",
        patch=plan["patch"]
    )


def test_idempotent():
    """Test that second insert is noop and pc1 is not called."""
    original = "existing code\n"
    snippet = "log.info('test');"
    marker = "log2"
    
    # First insert
    plan1 = plan_logging_insert("test.py", original, snippet, marker)
    pc1_mock1 = Mock(return_value=True)
    result1 = apply_patch(original, plan1["patch"], pc1_mock1)
    
    # Verify first insert called pc1
    assert pc1_mock1.call_count == 1
    
    # Second insert with same marker
    plan2 = plan_logging_insert("test.py", result1, snippet, marker)
    
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


def test_inverse_restores():
    """Test that inverse patch restores original text exactly."""
    original = "line1\nline2\nline3\n"
    snippet = "debug.log('inserted');"
    marker = "log3"
    
    # Insert snippet
    plan = plan_logging_insert("test.js", original, snippet, marker)
    pc1_insert = Mock(return_value=True)
    modified = apply_patch(original, plan["patch"], pc1_insert)
    
    # Verify modified is different
    assert modified != original
    
    # Apply inverse
    pc1_remove = Mock(return_value=True)
    restored = apply_inverse(modified, plan["inverse_patch"], pc1_remove)
    
    # Verify restored equals original exactly
    assert restored == original
    
    # Verify pc1 was called for remove
    assert pc1_remove.call_count == 1
    pc1_remove.assert_called_once_with(
        action="m5.log_snippet.remove",
        patch=plan["inverse_patch"]
    )


def test_pc1_enforced_insert():
    """Test that PC-1 denial raises PermissionError and text is unchanged."""
    original = "original content\n"
    snippet = "logger.debug('test');"
    marker = "log4"
    
    plan = plan_logging_insert("test.py", original, snippet, marker)
    
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
    snippet = "log('test');"
    marker = "log5"
    
    # First insert with permission
    plan = plan_logging_insert("test.js", original, snippet, marker)
    pc1_insert = Mock(return_value=True)
    modified = apply_patch(original, plan["patch"], pc1_insert)
    
    # Try to remove without permission
    pc1_remove = Mock(return_value=False)
    
    with pytest.raises(PermissionError):
        apply_inverse(modified, plan["inverse_patch"], pc1_remove)
    
    # Verify pc1 was called
    assert pc1_remove.call_count == 1


def test_pc1_call_count_noop():
    """Test that pc1 is called exactly once for insert/remove, zero for noop."""
    original = "content\n"
    snippet = "trace();"
    marker = "log6"
    
    # First insert - pc1 called once
    plan1 = plan_logging_insert("test.js", original, snippet, marker)
    pc1_insert = Mock(return_value=True)
    modified = apply_patch(original, plan1["patch"], pc1_insert)
    assert pc1_insert.call_count == 1
    
    # Second insert (noop) - pc1 NOT called
    plan2 = plan_logging_insert("test.js", modified, snippet, marker)
    pc1_noop = Mock(return_value=True)
    result = apply_patch(modified, plan2["patch"], pc1_noop)
    assert pc1_noop.call_count == 0
    assert result == modified
    
    # Remove - pc1 called once
    pc1_remove = Mock(return_value=True)
    restored = apply_inverse(modified, plan1["inverse_patch"], pc1_remove)
    assert pc1_remove.call_count == 1
    
    # Apply noop inverse (use the noop from plan2)
    pc1_noop_inverse = Mock(return_value=True)
    final = apply_inverse(modified, plan2["inverse_patch"], pc1_noop_inverse)
    assert pc1_noop_inverse.call_count == 0  # noop, so no call
    assert final == modified

