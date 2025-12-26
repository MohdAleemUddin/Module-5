import pytest

from edge.m5_observability.receipts.signature import (
    canonical_payload,
    sign_receipt,
    verify_receipt,
)


def _base_receipt():
    return {
        "module": "M5_observability_v1",
        "gate_id": "observability_gate_v1",
        "decision": {"outcome": "pass", "rationale": "ok"},
        "actor": {"type": "cli", "id": "user123", "client": "tests"},
        "inputs": {},
        "policy_snapshot_id": "snap-1",
        "timestamps": {"hw_monotonic_ms": 0},
    }


def test_sign_and_verify_round_trip():
    receipt = _base_receipt()
    signed = sign_receipt(receipt)

    assert "signature" in signed
    assert signed["signature"]["algo"] == "stub-sha256"
    assert len(signed["signature"]["value"]) == 64
    assert verify_receipt(signed) is True


def test_verify_fails_on_tamper():
    signed = sign_receipt(_base_receipt())
    signed["decision"]["rationale"] = "changed"

    assert verify_receipt(signed) is False


def test_unsupported_algo_raises():
    with pytest.raises(ValueError):
        sign_receipt(_base_receipt(), algo="sha1")


def test_malformed_signature_block():
    signed = sign_receipt(_base_receipt())
    signed["signature"]["value"] = "short"
    assert verify_receipt(signed) is False

    signed["signature"] = {"algo": "stub-sha256"}  # missing value
    assert verify_receipt(signed) is False

    signed.pop("signature")
    assert verify_receipt(signed) is False


def test_canonical_payload_excludes_signature():
    receipt = _base_receipt()
    signed = sign_receipt(receipt)
    payload = canonical_payload(signed)

    assert b"signature" not in payload
    # Deterministic ordering
    assert payload.decode("utf-8") == canonical_payload(receipt).decode("utf-8")


