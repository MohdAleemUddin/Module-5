def build_explainability(policy: dict, findings: dict, outcome: str) -> dict:
    fired_rules = []
    
    missing_signals = findings.get("missing_signals", [])
    pii_findings = findings.get("pii_findings", [])
    cardinality_findings = findings.get("cardinality_findings", [])
    dynamic_key_findings = findings.get("dynamic_key_findings", [])
    schema_violations = findings.get("schema_violations", [])
    telemetry_coverage_pct = findings.get("telemetry_coverage_pct", 100.0)
    
    require_correlation_id = policy.get("obs.require_correlation_id", False)
    require_hw_timestamp = policy.get("obs.require_hw_timestamp", False)
    min_cov_warn = policy.get("obs.min_telemetry_coverage_warn", 0.8)  # Fixed: use correct key
    if isinstance(min_cov_warn, float) and min_cov_warn <= 1.0:
        min_cov_warn = min_cov_warn * 100.0  # Convert to percentage
    min_cov_block = policy.get("obs.min_telemetry_coverage_block", 0.6)  # Fixed: use correct key
    if isinstance(min_cov_block, float) and min_cov_block <= 1.0:
        min_cov_block = min_cov_block * 100.0  # Convert to percentage
    disallow_dynamic_keys = policy.get("obs.disallow_dynamic_keys", False)
    cardinality_outcome = policy.get("obs.cardinality_outcome", "soft_block")
    
    # OBS-EXPL-0001 MissingCritical
    critical_missing = []
    if require_correlation_id:
        if "request_id" in missing_signals:
            critical_missing.append("request_id")
        if "trace_id" in missing_signals:
            critical_missing.append("trace_id")
    if require_hw_timestamp and "hw_ts_ms" in missing_signals:
        critical_missing.append("hw_ts_ms")
    
    if critical_missing:
        fired_rules.append({
            "rule_id": "OBS-EXPL-0001",
            "threshold": f"require_correlation_id={require_correlation_id},require_hw_timestamp={require_hw_timestamp}",
            "why": f"Missing critical signals: {','.join(sorted(critical_missing))}"
        })
    
    # OBS-EXPL-0004 PII
    if pii_findings:
        fired_rules.append({
            "rule_id": "OBS-EXPL-0004",
            "threshold": "disallow_pii=true",
            "why": f"Found {len(pii_findings)} PII/secret field(s)"
        })
    
    # OBS-EXPL-0005 DynamicKey
    if dynamic_key_findings and disallow_dynamic_keys:
        fired_rules.append({
            "rule_id": "OBS-EXPL-0005",
            "threshold": f"disallow_dynamic_keys={disallow_dynamic_keys}",
            "why": f"Found {len(dynamic_key_findings)} dynamic key(s)"
        })
    
    # OBS-EXPL-0006 HighCardinality
    if cardinality_findings:
        fired_rules.append({
            "rule_id": "OBS-EXPL-0006",
            "threshold": f"cardinality_outcome={cardinality_outcome}",
            "why": f"Found {len(cardinality_findings)} high-cardinality value(s)"
        })
    
    # OBS-EXPL-0007 SchemaViolation
    if schema_violations:
        fired_rules.append({
            "rule_id": "OBS-EXPL-0007",
            "threshold": "enforce_schema=true",
            "why": f"Found {len(schema_violations)} schema violation(s)"
        })
    
    # OBS-EXPL-0003 CoverageBelowBlock
    if telemetry_coverage_pct < min_cov_block:
        fired_rules.append({
            "rule_id": "OBS-EXPL-0003",
            "threshold": f"min_cov_block={min_cov_block}",
            "why": f"Coverage {telemetry_coverage_pct:.2f}% below block threshold {min_cov_block}%"
        })
    
    # OBS-EXPL-0002 CoverageBelowWarn
    if telemetry_coverage_pct < min_cov_warn:
        fired_rules.append({
            "rule_id": "OBS-EXPL-0002",
            "threshold": f"min_cov_warn={min_cov_warn}",
            "why": f"Coverage {telemetry_coverage_pct:.2f}% below warn threshold {min_cov_warn}%"
        })
    
    # OBS-EXPL-0008 MissingSignalsMinor
    optional_missing = sorted(set(missing_signals) - set(critical_missing))
    if optional_missing:
        fired_rules.append({
            "rule_id": "OBS-EXPL-0008",
            "threshold": "require_signals=optional",
            "why": f"Missing {len(optional_missing)} optional signal(s): {','.join(optional_missing)}"
        })
    
    # Sort fired_rules by rule_id
    fired_rules.sort(key=lambda x: x["rule_id"])
    
    # Determine smallest_fix
    smallest_fix = {"type": "none", "action_id": "", "summary": ""}
    
    if pii_findings:
        smallest_fix = {
            "type": "redaction",
            "action_id": "zeroui.m5.redactPii",
            "summary": "Redact PII/secret fields"
        }
    elif dynamic_key_findings and disallow_dynamic_keys:
        smallest_fix = {
            "type": "rewrite",
            "action_id": "zeroui.m5.rewriteLabels",
            "summary": "Rewrite dynamic label keys to static key + value field"
        }
    elif schema_violations:
        smallest_fix = {
            "type": "schema_fix",
            "action_id": "zeroui.m5.fixSchema",
            "summary": "Rename/normalize fields to schema"
        }
    elif critical_missing or missing_signals or telemetry_coverage_pct < min_cov_warn or telemetry_coverage_pct < min_cov_block:
        smallest_fix = {
            "type": "snippet",
            "action_id": "zeroui.m5.insertObsSnippet",
            "summary": "Add required observability signals"
        }
    
    return {
        "fired_rules": fired_rules,
        "smallest_fix": smallest_fix
    }

