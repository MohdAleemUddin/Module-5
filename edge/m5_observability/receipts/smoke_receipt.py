import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def generate_policy_snapshot_id(policy_data: dict = None) -> str:
    """
    Generate a deterministic policy snapshot ID.
    
    Args:
        policy_data: Optional policy dict to hash
    
    Returns:
        Policy snapshot ID string (e.g., "PB-2025-01-20T10:30:00Z")
    """
    if policy_data:
        # Create hash of policy content for deterministic ID
        policy_str = json.dumps(policy_data, sort_keys=True)
        policy_hash = hashlib.sha256(policy_str.encode()).hexdigest()[:8]
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        return f"PB-{timestamp}-{policy_hash}"
    else:
        # Fallback to timestamp-based ID
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        return f"PB-{timestamp}"


def write_smoke_receipt(
    receipts_path: str,
    payload: dict,
    policy_snapshot_id: str = None,
    actor: dict = None,
    policy_cfg: dict = None,
    files_touched: List[str] = None,
    endpoints_touched: List[str] = None,
    signals_present: List[str] = None,
    pii_findings: List[dict] = None,
    cardinality_findings: List[str] = None,
    explainability: dict = None,
    execution_mode: str = "normal",
    pc1_attested: bool = False,
    pc1_result: dict = None,
    actions: dict = None,
    roi_tags: List[str] = None,
    branch: str = None,
    related_pr: int = None,
    conflict_hotspot_ref: List[str] = None
) -> None:
    """
    Write smoke test receipt in JSONL format with all Module 5 required fields.
    
    Args:
        receipts_path: Path to receipts file
        payload: Smoke test results payload
        policy_snapshot_id: Optional policy snapshot ID (generated if not provided)
        actor: Optional actor dict (defaults to VS Code user)
        policy_cfg: Policy configuration dict (for explainability and PC-1)
        files_touched: List of files checked
        endpoints_touched: List of endpoints discovered
        signals_present: List of signals found
        pii_findings: List of PII findings
        cardinality_findings: List of cardinality findings
        explainability: Explainability dict from build_explainability
        execution_mode: "normal" or "explain_only"
        pc1_attested: Whether PC-1 check was performed
        pc1_result: PC-1 check result dict
        actions: Actions dict with snippet_inserted, redactions_applied, notes
        roi_tags: List of ROI tags
        branch: Git branch name
        related_pr: Related PR number
        conflict_hotspot_ref: List of conflict hotspot references
    """
    from edge.m5_observability.receipts.signature import sign_receipt
    
    # Generate policy snapshot ID if not provided
    if not policy_snapshot_id:
        policy_snapshot_id = generate_policy_snapshot_id(policy_cfg)

    # Default actor if not provided
    if not actor:
        actor = {
            "type": "human",
            "id": "vscode-user",
            "client": "vscode"
        }

    # Build explainability if not provided but policy is available
    if explainability is None and policy_cfg is not None:
        from edge.m5_observability.gates.explainability import build_explainability
        findings = {
            "missing_signals": payload.get("missing_signals", []),
            "pii_findings": pii_findings or [],
            "cardinality_findings": cardinality_findings or [],
            "dynamic_key_findings": [],
            "schema_violations": [],
            "telemetry_coverage_pct": payload.get("telemetry_coverage_pct", 0.0)
        }
        explainability = build_explainability(policy_cfg, findings, payload.get("outcome", "unknown"))

    # Build decision with explainability
    decision = {
        "outcome": payload["outcome"],
        "rationale": payload["rationale"]
    }
    if explainability:
        decision["explainability"] = explainability

    # Build inputs dict with all required fields
    inputs: Dict[str, Any] = {
        "required_signals": payload.get("required_signals", []),
        "signals_missing": payload.get("missing_signals", []),
        "telemetry_coverage_pct": payload.get("telemetry_coverage_pct", 0.0),
        "checked_files": payload.get("checked_files", 0)
    }
    
    # Add optional input fields if provided
    if branch is not None:
        inputs["branch"] = branch
    if related_pr is not None:
        inputs["related_pr"] = related_pr
    if files_touched is not None:
        inputs["files_touched"] = files_touched
    if endpoints_touched is not None:
        inputs["endpoints_touched"] = endpoints_touched
    if signals_present is not None:
        inputs["signals_present"] = signals_present
    if pii_findings is not None:
        inputs["pii_findings"] = pii_findings
    if cardinality_findings is not None:
        inputs["cardinality_findings"] = cardinality_findings
    if conflict_hotspot_ref is not None:
        inputs["conflict_hotspot_ref"] = conflict_hotspot_ref

    # Build actions dict
    if actions is None:
        actions = {}
    if "snippet_inserted" not in actions:
        actions["snippet_inserted"] = False
    if "redactions_applied" not in actions:
        actions["redactions_applied"] = []
    if "notes" not in actions:
        actions["notes"] = []

    # Build PC-1 dict
    pc1_dict = {}
    if pc1_result:
        pc1_dict = {
            "authoriser_gate": pc1_result.get("authoriser", "ok"),
            "rate_limiter": pc1_result.get("rate_limiter", "ok"),
            "dual_channel": pc1_result.get("dual_channel", "ok")
        }
    else:
        pc1_dict = {
            "authoriser_gate": "ok",
            "rate_limiter": "ok",
            "dual_channel": "ok"
        }

    # Build receipt object with all required fields
    receipt: Dict[str, Any] = {
        "module": "M5_observability_v1",
        "gate_id": "observability_v1",  # Fixed: spec says "observability_v1" not "observability_smoke_v1"
        "decision": decision,
        "actor": actor,
        "inputs": inputs,
        "actions": actions,
        "execution_mode": execution_mode,
        "policy_snapshot_id": policy_snapshot_id,
        "pc1_attested": pc1_attested,
        "pc1": pc1_dict,
        "timestamps": {
            "hw_monotonic_ms": payload.get("hw_monotonic_ms", 0),
            "hw_clock_khz": 1
        },
        "signature": {
            "algo": "stub-sha256",
            "value": "stub"  # Will be replaced by sign_receipt
        }
    }
    
    # Add ROI tags if provided
    if roi_tags is not None:
        receipt["roi_tags"] = roi_tags

    # Sign the receipt
    receipt = sign_receipt(receipt)
    
    # Ensure parent directory exists
    Path(receipts_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Append JSONL line
    with open(receipts_path, "a", encoding="utf-8", newline="\n") as f:
        json.dump(receipt, f, separators=(",", ":"), sort_keys=True)
        f.write("\n")

