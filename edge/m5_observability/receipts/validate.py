"""
Receipt validator for M5 (v1).
Performs minimal, strict presence checks before writing receipts.
"""

from typing import Any, Dict

from .schema import (
    REQUIRED_ACTOR,
    REQUIRED_DECISION,
    REQUIRED_SIGNATURE,
    REQUIRED_STRING_FIELDS,
    REQUIRED_TIMESTAMPS,
    REQUIRED_TOP_LEVEL,
)


def _require_strings(receipt: Dict[str, Any], keys: list[str], missing: list[str]) -> None:
    for key in keys:
        if key not in receipt or not isinstance(receipt[key], str):
            missing.append(key)


def _require_nested(
    receipt: Dict[str, Any], key: str, required_fields: list[str], missing: list[str]
) -> None:
    value = receipt.get(key)
    if not isinstance(value, dict):
        missing.extend([f"{key}.{field}" for field in required_fields])
        return

    for field in required_fields:
        if field not in value:
            missing.append(f"{key}.{field}")
        else:
            # Basic type checks for nested strings; tolerate numbers where specified elsewhere.
            if key in {"decision", "actor", "signature"} and not isinstance(value[field], str):
                missing.append(f"{key}.{field}")
            if key == "timestamps" and field == "hw_monotonic_ms":
                if not isinstance(value[field], (int, float)):
                    missing.append(f"{key}.{field}")


def validate_m5_receipt(receipt: Dict[str, Any]) -> None:
    """
    Validate a receipt dict against the minimal M5 schema.

    Raises:
        ValueError: if required fields are missing or invalid.
    """
    if not isinstance(receipt, dict):
        raise ValueError("Receipt must be a dict.")

    missing: list[str] = []

    # Top-level presence and string checks
    _require_strings(receipt, REQUIRED_STRING_FIELDS, missing)

    # Ensure required container keys exist (even if type-invalid)
    for key in REQUIRED_TOP_LEVEL:
        if key not in receipt and key not in missing:
            missing.append(key)

    # Nested checks
    _require_nested(receipt, "decision", REQUIRED_DECISION, missing)
    _require_nested(receipt, "actor", REQUIRED_ACTOR, missing)
    _require_nested(receipt, "timestamps", REQUIRED_TIMESTAMPS, missing)
    _require_nested(receipt, "signature", REQUIRED_SIGNATURE, missing)

    # inputs must be present and a dict
    inputs_val = receipt.get("inputs")
    if not isinstance(inputs_val, dict):
        missing.append("inputs")

    # Sort for deterministic messages
    if missing:
        unique_sorted = sorted(set(missing))
        raise ValueError(f"Missing required receipt fields: {', '.join(unique_sorted)}")


