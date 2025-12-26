"""
M4 hook to trigger M5 smoke tests and surface receipt linkage.
"""

from edge.m5_observability.checks import smoke_tests


def handle_m4_smoke_trigger(trigger: dict) -> dict:
    if not isinstance(trigger, dict):
        raise ValueError("trigger must be a dict")
    policy_snapshot_id = trigger.get("policy_snapshot_id")
    if not isinstance(policy_snapshot_id, str) or not policy_snapshot_id.strip():
        raise ValueError("policy_snapshot_id is required")

    return smoke_tests.run_m5_smoke_tests(policy_snapshot_id)


