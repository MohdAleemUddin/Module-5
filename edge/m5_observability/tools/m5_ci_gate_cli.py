import argparse
import json
import sys
from pathlib import Path

from edge.m5_observability.gates.explainability import build_explainability
from edge.m5_observability.gates.outcome_engine import eval_outcome
from edge.m5_observability.policy.loader import load_observability_policy


def main() -> int:
    parser = argparse.ArgumentParser(description="M5 CI Gate CLI")
    parser.add_argument("--policy", required=True, help="Policy JSON file path")
    parser.add_argument("--input", required=True, help="CI input findings JSON file path")
    parser.add_argument("--out", required=True, help="Output receipt JSONL file path")
    parser.add_argument("--gate-mode", required=True, choices=["Warn", "Soft", "Hard"], help="Gate mode")
    args = parser.parse_args()

    try:
        # Load policy
        policy = load_observability_policy(args.policy)
        
        # Load input findings
        input_path = Path(args.input)
        input_data = json.loads(input_path.read_text(encoding="utf-8"))
        
        # Extract findings (handle both cardinality_findings and cardinality_gate_outcome)
        cardinality_findings = input_data.get("cardinality_findings", [])
        if not cardinality_findings and "cardinality_gate_outcome" in input_data:
            # If cardinality_gate_outcome indicates issues, create findings list
            if input_data["cardinality_gate_outcome"] not in {"pass", "warn"}:
                cardinality_findings = ["cardinality_violation"]
        
        findings = {
            "missing_signals": input_data.get("missing_signals", []),
            "pii_findings": input_data.get("pii_findings", []),
            "cardinality_findings": cardinality_findings,
            "dynamic_key_findings": input_data.get("dynkey_violations", []),
            "schema_violations": input_data.get("schema_violations", []),
            "telemetry_coverage_pct": input_data.get("coverage", 100.0),
        }
        
        # Call eval_outcome
        outcome_result = eval_outcome(
            missing_signals=findings["missing_signals"],
            pii_findings=findings["pii_findings"],
            cardinality_findings=findings["cardinality_findings"],
            require_correlation_id=policy.get("obs.require_correlation_id", False),
            require_hw_timestamp=policy.get("obs.require_hw_timestamp", False),
            min_cov_warn=policy.get("obs.min_telemetry_coverage_warn", 0.8) * 100.0,
            min_cov_block=policy.get("obs.min_telemetry_coverage_block", 0.7) * 100.0,
            telemetry_coverage_pct=findings["telemetry_coverage_pct"],
        )
        
        outcome = outcome_result["outcome"]
        
        # Prepare policy dict for explainability (map keys)
        explainability_policy = {
            "obs.require_correlation_id": policy.get("obs.require_correlation_id", False),
            "obs.require_hw_timestamp": policy.get("obs.require_hw_timestamp", False),
            "obs.min_cov_warn": policy.get("obs.min_telemetry_coverage_warn", 0.8) * 100.0,
            "obs.min_cov_block": policy.get("obs.min_telemetry_coverage_block", 0.7) * 100.0,
            "obs.disallow_dynamic_keys": policy.get("obs.disallow_dynamic_keys", False),
            "obs.cardinality_outcome": "soft_block",
        }
        
        # Call build_explainability
        explainability = build_explainability(explainability_policy, findings, outcome)
        
        # Build receipt
        receipt = {
            "decision": {
                "outcome": outcome,
                "rationale": outcome_result["rationale"],
                "explainability": explainability
            }
        }
        
        # Write receipt JSONL
        out_path = Path(args.out)
        receipt_line = json.dumps(receipt, sort_keys=True)
        out_path.write_text(receipt_line + "\n", encoding="utf-8")
        
        # Determine exit code
        gate_mode = args.gate_mode
        if gate_mode == "Warn":
            return 0
        elif gate_mode == "Soft":
            return 1 if outcome in {"soft_block", "hard_block"} else 0
        else:  # Hard
            return 1 if outcome == "hard_block" else 0
            
    except Exception as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

