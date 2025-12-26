def eval_outcome(
    missing_signals: list[str],
    pii_findings: list[str],
    cardinality_findings: list[str],
    require_correlation_id: bool,
    require_hw_timestamp: bool,
    min_cov_warn: float,
    min_cov_block: float,
    telemetry_coverage_pct: float,
) -> dict:
    missing_sorted = sorted(missing_signals)
    missing_csv = ",".join(missing_sorted) if missing_sorted else "-"
    cov_rounded = round(telemetry_coverage_pct, 2)
    
    # Rule 1: Critical correlation (and timestamp) missing
    if require_correlation_id and "request_id" in missing_signals and "trace_id" in missing_signals:
        critical_missing = ["request_id", "trace_id"]
        if require_hw_timestamp and "hw_ts_ms" in missing_signals:
            critical_missing.append("hw_ts_ms")
        critical_missing = sorted(critical_missing)
        return {
            "outcome": "hard_block",
            "rule_id": "OBS-GATE-0001",
            "rationale": f"OBS: HARD [missing_critical={','.join(critical_missing)}; pii={len(pii_findings)}]"
        }
    
    # Rule 2: Hardware timestamp missing
    if require_hw_timestamp and "hw_ts_ms" in missing_signals:
        critical_missing = ["hw_ts_ms"]
        return {
            "outcome": "hard_block",
            "rule_id": "OBS-GATE-0001",
            "rationale": f"OBS: HARD [missing_critical={','.join(critical_missing)}; pii={len(pii_findings)}]"
        }
    
    # Rule 3: PII findings
    if pii_findings:
        critical_missing = sorted([s for s in missing_signals if s in ["request_id", "trace_id", "hw_ts_ms"]])
        critical_csv = ",".join(critical_missing) if critical_missing else "-"
        return {
            "outcome": "hard_block",
            "rule_id": "OBS-GATE-0001",
            "rationale": f"OBS: HARD [missing_critical={critical_csv}; pii={len(pii_findings)}]"
        }
    
    # Rule 4: Cardinality findings
    if cardinality_findings:
        return {
            "outcome": "soft_block",
            "rule_id": "OBS-GATE-0001",
            "rationale": f"OBS: SOFT [coverage={cov_rounded}; missing={missing_csv}; card={len(cardinality_findings)}]"
        }
    
    # Rule 5: Coverage below block threshold
    if telemetry_coverage_pct < min_cov_block:
        return {
            "outcome": "soft_block",
            "rule_id": "OBS-GATE-0001",
            "rationale": f"OBS: SOFT [coverage={cov_rounded}; missing={missing_csv}; card=0]"
        }
    
    # Rule 6: Coverage below warn threshold OR missing signals
    if telemetry_coverage_pct < min_cov_warn or len(missing_signals) > 0:
        return {
            "outcome": "warn",
            "rule_id": "OBS-GATE-0001",
            "rationale": f"OBS: WARN [coverage={cov_rounded}; missing={missing_csv}]"
        }
    
    # Rule 7: Pass
    return {
        "outcome": "pass",
        "rule_id": "OBS-GATE-0001",
        "rationale": "OBS: PASS"
    }

