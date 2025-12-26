import pytest
from edge.m5_observability.checks.parity import enforce_parity


def test_human_always_ok():
    """Test that human actor always returns 'ok' (parity not applicable)."""
    result = enforce_parity("human", "pass", "pass")
    assert result == "ok"
    
    # Human should be ok even with different outcomes
    result2 = enforce_parity("human", "hard_block", "pass")
    assert result2 == "ok"


def test_agent_violation_lower_severity():
    """Test that agent with lower severity outcome returns 'violation'."""
    # Agent has "warn" but human had "soft_block" (warn < soft_block)
    result = enforce_parity("agent", "soft_block", "warn")
    assert result == "violation"


def test_agent_ok_higher_severity():
    """Test that agent with higher severity outcome returns 'ok'."""
    # Agent has "soft_block" but human had "warn" (soft_block >= warn)
    result = enforce_parity("agent", "warn", "soft_block")
    assert result == "ok"


def test_invalid_actor_type():
    """Test that invalid actor_type raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        enforce_parity("robot", "pass", "pass")
    
    assert "Invalid actor_type" in str(exc_info.value)
    assert "robot" in str(exc_info.value)


def test_invalid_outcome_human():
    """Test that invalid outcome string raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        enforce_parity("human", "invalid_outcome", "pass")
    
    assert "Invalid human_outcome" in str(exc_info.value)


def test_invalid_outcome_actor():
    """Test that invalid actor outcome string raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        enforce_parity("agent", "pass", "invalid_outcome")
    
    assert "Invalid actor_outcome" in str(exc_info.value)


def test_missing_latency_parity():
    """Test missing latency parity: both have soft_block outcome."""
    # When latency is missing, treat as soft_block for both
    result = enforce_parity("agent", "soft_block", "soft_block")
    assert result == "ok"


def test_agent_same_severity():
    """Test that agent with same severity as human returns 'ok'."""
    # Test all levels with same severity
    assert enforce_parity("agent", "pass", "pass") == "ok"
    assert enforce_parity("agent", "warn", "warn") == "ok"
    assert enforce_parity("agent", "soft_block", "soft_block") == "ok"
    assert enforce_parity("agent", "hard_block", "hard_block") == "ok"


def test_agent_all_violations():
    """Test various violation scenarios."""
    # pass < warn < soft_block < hard_block
    assert enforce_parity("agent", "warn", "pass") == "violation"
    assert enforce_parity("agent", "soft_block", "pass") == "violation"
    assert enforce_parity("agent", "soft_block", "warn") == "violation"
    assert enforce_parity("agent", "hard_block", "pass") == "violation"
    assert enforce_parity("agent", "hard_block", "warn") == "violation"
    assert enforce_parity("agent", "hard_block", "soft_block") == "violation"


def test_agent_all_ok_cases():
    """Test various ok scenarios where agent meets or exceeds human severity."""
    # Agent equal or higher severity
    assert enforce_parity("agent", "pass", "warn") == "ok"
    assert enforce_parity("agent", "pass", "soft_block") == "ok"
    assert enforce_parity("agent", "pass", "hard_block") == "ok"
    assert enforce_parity("agent", "warn", "hard_block") == "ok"
    assert enforce_parity("agent", "soft_block", "hard_block") == "ok"


def test_deterministic():
    """Test that output is deterministic (no random/time data)."""
    result1 = enforce_parity("agent", "warn", "soft_block")
    result2 = enforce_parity("agent", "warn", "soft_block")
    
    assert result1 == result2
    assert result1 == "ok"

