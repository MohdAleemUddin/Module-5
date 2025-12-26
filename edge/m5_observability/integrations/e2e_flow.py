def simulate_save_fix_pass(
    required_signals: list[str],
    before_text: str,
    after_text: str,
    policy_snapshot_id: str,
    require_correlation_id: bool,
    require_hw_timestamp: bool,
) -> dict:
    # Find missing signals in before/after text
    def find_missing(text: str, signals: list[str]) -> list[str]:
        missing = []
        for signal in signals:
            if signal not in text:
                missing.append(signal)
        return sorted(missing)
    
    missing_before = find_missing(before_text, required_signals)
    missing_after = find_missing(after_text, required_signals)
    
    # Calculate coverage
    def calc_coverage(present: int, required: int) -> float:
        if required == 0:
            return 0.0
        return round((present / required) * 100.0, 2)
    
    present_before = len(required_signals) - len(missing_before)
    present_after = len(required_signals) - len(missing_after)
    coverage_before = calc_coverage(present_before, len(required_signals))
    coverage_after = calc_coverage(present_after, len(required_signals))
    
    # Determine outcome
    if len(missing_after) == 0:
        outcome = "pass"
    elif require_correlation_id and ("trace_id" in missing_after or "request_id" in missing_after):
        outcome = "soft_block"
    elif require_hw_timestamp and "hw_ts_ms" in missing_after:
        outcome = "soft_block"
    else:
        outcome = "warn"
    
    # Build receipt
    receipt = {
        "decision": {
            "outcome": outcome
        },
        "inputs": {
            "signals_missing_before": missing_before,
            "signals_missing_after": missing_after,
            "telemetry_coverage_pct_before": coverage_before,
            "telemetry_coverage_pct_after": coverage_after
        },
        "actions": {
            "snippet_inserted": len(missing_before) > 0 and len(missing_after) == 0
        },
        "policy_snapshot_id": policy_snapshot_id
    }
    
    return receipt

