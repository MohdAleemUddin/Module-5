import pytest

from edge.m5_observability.receipts.validate import validate_m5_receipt


def _valid_receipt() -> dict:
    return {
        "module": "M5_observability_v1",
        "gate_id": "observability_gate_v1",
        "decision": {"outcome": "pass", "rationale": "ok"},
        "actor": {"type": "cli", "id": "user123", "client": "tests"},
        "inputs": {},
        "policy_snapshot_id": "snap-1",
        "timestamps": {"hw_monotonic_ms": 0},
        "signature": {"algo": "stub-sha256", "value": "stub"},
    }


def test_valid_minimal_receipt_passes():
    receipt = _valid_receipt()
    validate_m5_receipt(receipt)  # Should not raise


def test_missing_single_field_raises():
    receipt = _valid_receipt()
    receipt["actor"].pop("client")

    with pytest.raises(ValueError) as excinfo:
        validate_m5_receipt(receipt)

    assert "actor.client" in str(excinfo.value)


def test_missing_multiple_fields_sorted():
    receipt = _valid_receipt()
    receipt.pop("gate_id")
    receipt["decision"].pop("rationale")

    with pytest.raises(ValueError) as excinfo:
        validate_m5_receipt(receipt)

    message = str(excinfo.value)
    # Deterministic ordering
    assert "decision.rationale" in message
    assert "gate_id" in message
    assert message.index("decision.rationale") < message.index("gate_id")


