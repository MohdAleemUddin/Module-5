import pytest
from edge.m5_observability.gates.explainability import build_explainability


def test_hard_block_critical():
    """HARD block due to missing critical signals."""
    policy = {
        "obs.require_correlation_id": True,
        "obs.require_hw_timestamp": False,
        "obs.min_cov_warn": 80.0,
        "obs.min_cov_block": 70.0,
    }
    findings = {
        "missing_signals": ["request_id", "trace_id", "signal1"],
        "pii_findings": [],
        "cardinality_findings": [],
        "telemetry_coverage_pct": 90.0,
    }
    outcome = "hard_block"
    
    result = build_explainability(policy, findings, outcome)
    
    assert len(result["fired_rules"]) == 2
    assert result["fired_rules"][0]["rule_id"] == "OBS-EXPL-0001"
    assert result["fired_rules"][1]["rule_id"] == "OBS-EXPL-0008"
    assert result["smallest_fix"]["type"] == "snippet"
    assert result["smallest_fix"]["action_id"] == "zeroui.m5.insertObsSnippet"


def test_hard_block_pii():
    """HARD block due to PII findings."""
    policy = {
        "obs.require_correlation_id": False,
        "obs.require_hw_timestamp": False,
        "obs.min_cov_warn": 80.0,
        "obs.min_cov_block": 70.0,
        "obs.disallow_dynamic_keys": False,
    }
    findings = {
        "missing_signals": [],
        "pii_findings": ["email", "ssn"],
        "cardinality_findings": [],
        "telemetry_coverage_pct": 95.0,
    }
    outcome = "hard_block"
    
    result = build_explainability(policy, findings, outcome)
    
    assert len(result["fired_rules"]) == 1
    assert result["fired_rules"][0]["rule_id"] == "OBS-EXPL-0004"
    assert result["fired_rules"][0]["threshold"] == "disallow_pii=true"
    assert result["smallest_fix"]["type"] == "redaction"
    assert result["smallest_fix"]["action_id"] == "zeroui.m5.redactPii"
    assert result["smallest_fix"]["summary"] == "Redact PII/secret fields"


def test_soft_block_schema_high_card():
    """SOFT block due to schema violations and high cardinality."""
    policy = {
        "obs.require_correlation_id": False,
        "obs.require_hw_timestamp": False,
        "obs.min_cov_warn": 80.0,
        "obs.min_cov_block": 70.0,
        "obs.disallow_dynamic_keys": False,
        "obs.cardinality_outcome": "soft_block",
    }
    findings = {
        "missing_signals": [],
        "pii_findings": [],
        "cardinality_findings": ["high_card_value: uuid-123"],
        "schema_violations": ["field_name_mismatch"],
        "telemetry_coverage_pct": 85.0,
    }
    outcome = "soft_block"
    
    result = build_explainability(policy, findings, outcome)
    
    assert len(result["fired_rules"]) == 2
    rule_ids = [r["rule_id"] for r in result["fired_rules"]]
    assert "OBS-EXPL-0006" in rule_ids
    assert "OBS-EXPL-0007" in rule_ids
    assert result["smallest_fix"]["type"] == "schema_fix"
    assert result["smallest_fix"]["action_id"] == "zeroui.m5.fixSchema"

