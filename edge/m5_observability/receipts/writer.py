"""
Receipt writer for M5 (v1) — append-only JSONL with validation.
"""

import json
import os
from typing import Any, Dict

from .validate import validate_m5_receipt


def append_receipt_jsonl(path: str, receipt: Dict[str, Any], *, fsync: bool = True) -> None:
    """
    Append a validated receipt to a JSONL file.
    """
    # Validate first (also ensures required keys are present)
    validate_m5_receipt(receipt)

    # Explicitly ensure required anchored fields exist (no defaults)
    if "policy_snapshot_id" not in receipt:
        raise ValueError("Missing required receipt field: policy_snapshot_id")
    if "timestamps" not in receipt or "hw_monotonic_ms" not in receipt["timestamps"]:
        raise ValueError("Missing required receipt field: timestamps.hw_monotonic_ms")

    line = json.dumps(receipt, separators=(",", ":"), sort_keys=True) + "\n"

    # Append-only write
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(line)
        fh.flush()
        if fsync:
            os.fsync(fh.fileno())


