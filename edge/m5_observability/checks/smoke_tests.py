"""
Stubbed M5 smoke tests runner for CI hook.
Deterministic and side-effect free.
"""


def run_m5_smoke_tests(policy_snapshot_id: str) -> dict:
    """
    Run (stub) smoke tests and return a receipt-like dict.
    """
    return {
        "module": "M5_observability_v1",
        "gate_id": "observability_v1",
        "decision": {"outcome": "pass", "rationale": "OBS: SMOKE_TESTS_PASS"},
        "actor": {"type": "agent", "id": "m4", "client": "ci"},
        "inputs": {"checks": ["smoke_stub"], "telemetry_coverage_pct": 0.0, "signals_missing": []},
        "execution_mode": "normal",
        "policy_snapshot_id": policy_snapshot_id,
        "timestamps": {"hw_monotonic_ms": 1},
        "signature": {"algo": "stub-sha256", "value": "x"},
    }


