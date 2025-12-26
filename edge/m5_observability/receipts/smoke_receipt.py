import json
from pathlib import Path


def write_smoke_receipt(receipts_path: str, payload: dict) -> None:
    """
    Write smoke test receipt in JSONL format.
    
    Args:
        receipts_path: Path to receipts file
        payload: Smoke test results payload
    """
    # Build receipt object
    receipt = {
        "module": "M5_observability_v1",
        "gate_id": "observability_smoke_v1",
        "decision": {
            "outcome": payload["outcome"],
            "rationale": payload["rationale"]
        },
        "inputs": {
            "required_signals": payload["required_signals"],
            "missing_signals": payload["missing_signals"],
            "telemetry_coverage_pct": payload["telemetry_coverage_pct"],
            "checked_files": payload["checked_files"]
        },
        "timestamps": {
            "hw_monotonic_ms": 0
        },
        "signature": {
            "algo": "stub-sha256",
            "value": "stub"
        }
    }
    
    # Ensure parent directory exists
    Path(receipts_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Append JSONL line
    with open(receipts_path, "a", encoding="utf-8") as f:
        json.dump(receipt, f, sort_keys=True)
        f.write("\n")

