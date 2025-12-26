import pytest
from edge.m5_observability.integrations.e2e_flow import simulate_save_fix_pass


def test_save_fix_pass_flow():
    """Test E2E flow: before missing signals => after all present => pass."""
    required_signals = ["latency_ms", "status", "error_code", "request_id", "trace_id", "hw_ts_ms"]
    
    before_text = "latency_ms status error_code request_id"
    after_text = "latency_ms status error_code request_id trace_id hw_ts_ms"
    
    policy_snapshot_id = "policy_v1"
    require_correlation_id = True
    require_hw_timestamp = True
    
    receipt = simulate_save_fix_pass(
        required_signals=required_signals,
        before_text=before_text,
        after_text=after_text,
        policy_snapshot_id=policy_snapshot_id,
        require_correlation_id=require_correlation_id,
        require_hw_timestamp=require_hw_timestamp
    )
    
    # Verify outcome
    assert receipt["decision"]["outcome"] == "pass"
    
    # Verify missing signals
    assert "trace_id" in receipt["inputs"]["signals_missing_before"]
    assert "hw_ts_ms" in receipt["inputs"]["signals_missing_before"]
    assert len(receipt["inputs"]["signals_missing_after"]) == 0
    
    # Verify coverage
    coverage_before = receipt["inputs"]["telemetry_coverage_pct_before"]
    coverage_after = receipt["inputs"]["telemetry_coverage_pct_after"]
    assert coverage_after > coverage_before
    assert coverage_before == round((4 / 6) * 100.0, 2)
    assert coverage_after == 100.0
    
    # Verify actions
    assert receipt["actions"]["snippet_inserted"] is True
    
    # Verify policy snapshot
    assert receipt["policy_snapshot_id"] == policy_snapshot_id
    
    # Verify all required fields exist
    assert "decision" in receipt
    assert "inputs" in receipt
    assert "actions" in receipt
    assert "policy_snapshot_id" in receipt


def test_soft_block_outcome():
    """Test that missing critical signals after fix results in soft_block."""
    required_signals = ["latency_ms", "status", "error_code", "request_id", "trace_id", "hw_ts_ms"]
    
    before_text = "latency_ms status error_code"
    after_text = "latency_ms status error_code request_id"
    
    receipt = simulate_save_fix_pass(
        required_signals=required_signals,
        before_text=before_text,
        after_text=after_text,
        policy_snapshot_id="policy_v1",
        require_correlation_id=True,
        require_hw_timestamp=True
    )
    
    assert receipt["decision"]["outcome"] == "soft_block"
    assert "trace_id" in receipt["inputs"]["signals_missing_after"]
    assert "hw_ts_ms" in receipt["inputs"]["signals_missing_after"]

