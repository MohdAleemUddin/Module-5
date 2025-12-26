import pytest
from edge.m5_observability.gates.outcome_engine import eval_outcome


@pytest.mark.parametrize(
    "missing_signals,pii_findings,cardinality_findings,require_correlation_id,require_hw_timestamp,min_cov_warn,min_cov_block,telemetry_coverage_pct,expected_outcome,expected_rationale",
    [
        # PASS cases
        ([], [], [], False, False, 80.0, 70.0, 90.0, "pass", "OBS: PASS"),
        ([], [], [], True, False, 80.0, 70.0, 90.0, "pass", "OBS: PASS"),
        
        # WARN cases
        (["signal1"], [], [], False, False, 80.0, 70.0, 85.0, "warn", "OBS: WARN [coverage=85.0; missing=signal1]"),
        ([], [], [], False, False, 80.0, 70.0, 75.0, "warn", "OBS: WARN [coverage=75.0; missing=-]"),
        (["a", "b"], [], [], False, False, 80.0, 70.0, 85.0, "warn", "OBS: WARN [coverage=85.0; missing=a,b]"),
        
        # SOFT_BLOCK cases
        ([], [], ["card1"], False, False, 80.0, 70.0, 85.0, "soft_block", "OBS: SOFT [coverage=85.0; missing=-; card=1]"),
        (["signal1"], [], ["card1", "card2"], False, False, 80.0, 70.0, 85.0, "soft_block", "OBS: SOFT [coverage=85.0; missing=signal1; card=2]"),
        ([], [], [], False, False, 80.0, 70.0, 65.0, "soft_block", "OBS: SOFT [coverage=65.0; missing=-; card=0]"),
        (["signal1"], [], [], False, False, 80.0, 70.0, 65.0, "soft_block", "OBS: SOFT [coverage=65.0; missing=signal1; card=0]"),
        
        # HARD_BLOCK cases
        (["request_id", "trace_id"], [], [], True, False, 80.0, 70.0, 90.0, "hard_block", "OBS: HARD [missing_critical=request_id,trace_id; pii=0]"),
        (["hw_ts_ms"], [], [], False, True, 80.0, 70.0, 90.0, "hard_block", "OBS: HARD [missing_critical=hw_ts_ms; pii=0]"),
        ([], ["pii1"], [], False, False, 80.0, 70.0, 90.0, "hard_block", "OBS: HARD [missing_critical=-; pii=1]"),
        (["signal1"], ["pii1", "pii2"], [], False, False, 80.0, 70.0, 90.0, "hard_block", "OBS: HARD [missing_critical=-; pii=2]"),
        (["request_id", "trace_id", "hw_ts_ms"], ["pii1"], [], True, True, 80.0, 70.0, 90.0, "hard_block", "OBS: HARD [missing_critical=hw_ts_ms,request_id,trace_id; pii=1]"),
    ],
)
def test_eval_outcome(
    missing_signals,
    pii_findings,
    cardinality_findings,
    require_correlation_id,
    require_hw_timestamp,
    min_cov_warn,
    min_cov_block,
    telemetry_coverage_pct,
    expected_outcome,
    expected_rationale,
):
    result = eval_outcome(
        missing_signals=missing_signals,
        pii_findings=pii_findings,
        cardinality_findings=cardinality_findings,
        require_correlation_id=require_correlation_id,
        require_hw_timestamp=require_hw_timestamp,
        min_cov_warn=min_cov_warn,
        min_cov_block=min_cov_block,
        telemetry_coverage_pct=telemetry_coverage_pct,
    )
    
    assert result["outcome"] == expected_outcome
    assert result["rule_id"] == "OBS-GATE-0001"
    assert result["rationale"] == expected_rationale

