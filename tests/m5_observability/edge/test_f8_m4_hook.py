import pytest

from edge.m5_observability.integrations.m4_hook import handle_m4_smoke_trigger
from edge.m5_observability.checks import smoke_tests


def test_handle_trigger_runs_smoke_and_links_snapshot(monkeypatch):
    calls = {"count": 0}

    def fake_run(snapshot_id: str):
        calls["count"] += 1
        return {
            "module": "M5_observability_v1",
            "gate_id": "observability_v1",
            "decision": {"outcome": "pass", "rationale": "OBS: SMOKE_TESTS_PASS"},
            "actor": {"type": "agent", "id": "m4", "client": "ci"},
            "inputs": {"checks": ["smoke_stub"], "telemetry_coverage_pct": 0.0, "signals_missing": []},
            "execution_mode": "normal",
            "policy_snapshot_id": snapshot_id,
            "timestamps": {"hw_monotonic_ms": 1},
            "signature": {"algo": "stub-sha256", "value": "x"},
        }

    monkeypatch.setattr(smoke_tests, "run_m5_smoke_tests", fake_run)

    trigger = {"policy_snapshot_id": "PB-123"}
    result = handle_m4_smoke_trigger(trigger)

    assert calls["count"] == 1
    assert result["policy_snapshot_id"] == "PB-123"
    assert result["inputs"]["checks"] == ["smoke_stub"]

    # Linkage check with a dummy M4 receipt using same snapshot id
    m4_receipt = {"policy_snapshot_id": "PB-123"}
    assert m4_receipt["policy_snapshot_id"] == result["policy_snapshot_id"]


def test_missing_snapshot_id_raises():
    with pytest.raises(ValueError):
        handle_m4_smoke_trigger({})

    with pytest.raises(ValueError):
        handle_m4_smoke_trigger({"policy_snapshot_id": ""})


