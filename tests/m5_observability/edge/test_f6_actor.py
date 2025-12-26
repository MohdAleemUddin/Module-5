import pytest
from edge.m5_observability.receipts.actor import build_actor


def test_human_actor():
    """Test that human actor is correctly built."""
    result = build_actor("human", "user@example.com", "vscode")
    
    assert result["type"] == "human"
    assert result["id"] == "user@example.com"
    assert result["client"] == "vscode"
    
    # Verify exact keys
    assert set(result.keys()) == {"type", "id", "client"}


def test_agent_actor():
    """Test that agent actor is correctly built."""
    result = build_actor("agent", "bot-123", "github-actions")
    
    assert result["type"] == "agent"
    assert result["id"] == "bot-123"
    assert result["client"] == "github-actions"
    
    # Verify exact keys
    assert set(result.keys()) == {"type", "id", "client"}


def test_invalid_actor_type():
    """Test that invalid actor_type raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        build_actor("robot", "id-123", "client-app")
    
    assert "Invalid actor_type" in str(exc_info.value)
    assert "robot" in str(exc_info.value)


def test_empty_actor_id():
    """Test that empty actor_id raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        build_actor("human", "", "vscode")
    
    assert "actor_id" in str(exc_info.value)
    assert "non-empty" in str(exc_info.value)


def test_empty_actor_client():
    """Test that empty actor_client raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        build_actor("human", "user@example.com", "")
    
    assert "actor_client" in str(exc_info.value)
    assert "non-empty" in str(exc_info.value)


def test_deterministic():
    """Test that output is deterministic (no random/time data)."""
    result1 = build_actor("human", "test-user", "test-client")
    result2 = build_actor("human", "test-user", "test-client")
    
    # Should be identical
    assert result1 == result2
    
    # No unexpected keys
    assert len(result1) == 3


def test_multiple_calls_different_inputs():
    """Test that different inputs produce different outputs correctly."""
    human_result = build_actor("human", "human-1", "client-1")
    agent_result = build_actor("agent", "agent-1", "client-2")
    
    assert human_result["type"] == "human"
    assert agent_result["type"] == "agent"
    assert human_result["id"] != agent_result["id"]
    assert human_result["client"] != agent_result["client"]

