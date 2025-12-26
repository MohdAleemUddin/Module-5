import pytest
from edge.m5_observability.checks.required_signals import check_required_signals


def test_all_signals_present():
    """Test when surface_text contains all required signals."""
    required_signals = ["latency_ms", "status", "error_code", "request_id", "trace_id", "hw_ts_ms"]
    surface_text = """
    Function logs: latency_ms=120, status=200, error_code=0, 
    request_id=abc123, trace_id=xyz789, hw_ts_ms=1640000000000
    """
    
    result = check_required_signals(surface_text, required_signals)
    
    assert result["signals_missing"] == []
    assert set(result["signals_present"]) == set(required_signals)
    assert result["signals_present"] == sorted(result["signals_present"])


def test_some_signals_missing():
    """Test when some signals are missing (trace_id and hw_ts_ms)."""
    required_signals = ["latency_ms", "status", "error_code", "request_id", "trace_id", "hw_ts_ms"]
    surface_text = """
    Function logs: latency_ms=120, status=200, error_code=0, request_id=abc123
    """
    
    result = check_required_signals(surface_text, required_signals)
    
    assert result["signals_missing"] == ["hw_ts_ms", "trace_id"]
    assert "latency_ms" in result["signals_present"]
    assert "status" in result["signals_present"]
    assert result["signals_missing"] == sorted(result["signals_missing"])


def test_empty_required_signals():
    """Test when required_signals is empty."""
    required_signals = []
    surface_text = "latency_ms=120, status=200"
    
    result = check_required_signals(surface_text, required_signals)
    
    assert result["signals_present"] == []
    assert result["signals_missing"] == []


def test_duplicate_required_signals():
    """Test that duplicates in required_signals produce unique sorted outputs."""
    required_signals = ["latency_ms", "status", "latency_ms", "error_code", "status"]
    surface_text = "latency_ms=120, status=200"
    
    result = check_required_signals(surface_text, required_signals)
    
    # Check uniqueness
    assert len(result["signals_present"]) == len(set(result["signals_present"]))
    assert len(result["signals_missing"]) == len(set(result["signals_missing"]))
    
    # Check sorted
    assert result["signals_present"] == sorted(result["signals_present"])
    assert result["signals_missing"] == sorted(result["signals_missing"])
    
    # Check correctness
    assert "latency_ms" in result["signals_present"]
    assert "status" in result["signals_present"]
    assert "error_code" in result["signals_missing"]

