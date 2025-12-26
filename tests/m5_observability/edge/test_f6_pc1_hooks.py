import pytest
from unittest.mock import Mock
from edge.m5_observability.pc1.hooks import pc1_prewrite_check


def test_both_ok():
    """Test that when both checks pass, allowed is True and both are called once."""
    # Mock authoriser that returns ok
    auth_mock = Mock(return_value={"ok": True, "code": "AUTH_OK"})
    
    # Mock rate limiter that returns ok
    rate_mock = Mock(return_value={"ok": True, "code": "RATE_OK"})
    
    # Call the function
    result = pc1_prewrite_check(auth_mock, rate_mock)
    
    # Verify result
    assert result["allowed"] is True
    assert result["authoriser"] == "ok"
    assert result["rate_limiter"] == "ok"
    
    # Verify both were called exactly once
    assert auth_mock.call_count == 1
    assert rate_mock.call_count == 1


def test_authoriser_fail():
    """Test that when authoriser fails, rate limiter is not called."""
    # Mock authoriser that fails
    auth_mock = Mock(return_value={"ok": False, "code": "AUTH_DENIED"})
    
    # Mock rate limiter
    rate_mock = Mock(return_value={"ok": True, "code": "RATE_OK"})
    
    # Call the function
    result = pc1_prewrite_check(auth_mock, rate_mock)
    
    # Verify result
    assert result["allowed"] is False
    assert result["authoriser"] == "AUTH_DENIED"
    assert result["rate_limiter"] == "SKIPPED"
    
    # Verify authoriser was called once, rate limiter not called
    assert auth_mock.call_count == 1
    assert rate_mock.call_count == 0


def test_rate_limiter_fail():
    """Test that when rate limiter fails, both are called and result shows failure."""
    # Mock authoriser that passes
    auth_mock = Mock(return_value={"ok": True, "code": "AUTH_OK"})
    
    # Mock rate limiter that fails
    rate_mock = Mock(return_value={"ok": False, "code": "RATE_EXCEEDED"})
    
    # Call the function
    result = pc1_prewrite_check(auth_mock, rate_mock)
    
    # Verify result
    assert result["allowed"] is False
    assert result["authoriser"] == "ok"
    assert result["rate_limiter"] == "RATE_EXCEEDED"
    
    # Verify both were called exactly once
    assert auth_mock.call_count == 1
    assert rate_mock.call_count == 1


def test_deterministic_behavior():
    """Test that same inputs produce same outputs (deterministic)."""
    # Create consistent mocks
    auth_mock = Mock(return_value={"ok": True, "code": "AUTH_OK"})
    rate_mock = Mock(return_value={"ok": False, "code": "RATE_LIMITED"})
    
    # Call twice
    result1 = pc1_prewrite_check(auth_mock, rate_mock)
    result2 = pc1_prewrite_check(auth_mock, rate_mock)
    
    # Results should be identical
    assert result1 == result2
    assert result1["allowed"] is False
    assert result1["rate_limiter"] == "RATE_LIMITED"


def test_various_error_codes():
    """Test various error codes are correctly propagated."""
    # Test different authoriser error codes
    auth_errors = ["PERMISSION_DENIED", "INVALID_TOKEN", "EXPIRED_CREDENTIALS"]
    
    for error_code in auth_errors:
        auth_mock = Mock(return_value={"ok": False, "code": error_code})
        rate_mock = Mock(return_value={"ok": True, "code": "RATE_OK"})
        
        result = pc1_prewrite_check(auth_mock, rate_mock)
        
        assert result["allowed"] is False
        assert result["authoriser"] == error_code
        assert result["rate_limiter"] == "SKIPPED"
    
    # Test different rate limiter error codes
    rate_errors = ["QUOTA_EXCEEDED", "TOO_MANY_REQUESTS", "BURST_LIMIT"]
    
    for error_code in rate_errors:
        auth_mock = Mock(return_value={"ok": True, "code": "AUTH_OK"})
        rate_mock = Mock(return_value={"ok": False, "code": error_code})
        
        result = pc1_prewrite_check(auth_mock, rate_mock)
        
        assert result["allowed"] is False
        assert result["authoriser"] == "ok"
        assert result["rate_limiter"] == error_code


def test_call_order():
    """Test that authoriser is always called before rate limiter."""
    call_order = []
    
    def auth_fn():
        call_order.append("auth")
        return {"ok": True, "code": "AUTH_OK"}
    
    def rate_fn():
        call_order.append("rate")
        return {"ok": True, "code": "RATE_OK"}
    
    pc1_prewrite_check(auth_fn, rate_fn)
    
    # Verify order
    assert call_order == ["auth", "rate"]


def test_short_circuit_on_auth_fail():
    """Test that rate limiter is truly skipped when auth fails (short-circuit)."""
    auth_mock = Mock(return_value={"ok": False, "code": "NO_AUTH"})
    
    # Rate limiter that would fail if called
    rate_mock = Mock(side_effect=Exception("Should not be called"))
    
    # This should not raise an exception because rate limiter is not called
    result = pc1_prewrite_check(auth_mock, rate_mock)
    
    assert result["allowed"] is False
    assert result["rate_limiter"] == "SKIPPED"
    assert rate_mock.call_count == 0

