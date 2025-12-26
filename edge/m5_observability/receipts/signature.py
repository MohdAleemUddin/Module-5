"""
Signature utilities for M5 receipts (stub-sha256).
Deterministic; no IO; no mutation of inputs.
"""

import copy
import hashlib
import json
from typing import Any, Dict

SUPPORTED_ALGO = "stub-sha256"


def canonical_payload(receipt: Dict[str, Any]) -> bytes:
    """
    Return canonical JSON bytes of the receipt without the signature block.
    """
    payload = copy.deepcopy(receipt)
    payload.pop("signature", None)
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def sign_receipt(receipt: Dict[str, Any], algo: str = SUPPORTED_ALGO) -> Dict[str, Any]:
    """
    Produce a new receipt dict with signature block added.
    """
    if algo != SUPPORTED_ALGO:
        raise ValueError(f"Unsupported signature algorithm: {algo}")

    digest = hashlib.sha256(canonical_payload(receipt)).hexdigest()
    signed = copy.deepcopy(receipt)
    signed["signature"] = {"algo": SUPPORTED_ALGO, "value": digest}
    return signed


def verify_receipt(receipt: Dict[str, Any]) -> bool:
    """
    Verify the receipt signature; returns False on any invalidity.
    """
    sig = receipt.get("signature")
    if not isinstance(sig, dict):
        return False
    algo = sig.get("algo")
    value = sig.get("value")
    if algo != SUPPORTED_ALGO or not isinstance(value, str) or len(value) != 64:
        return False

    expected = hashlib.sha256(canonical_payload(receipt)).hexdigest()
    return value == expected


