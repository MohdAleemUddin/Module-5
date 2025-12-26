"""
Minimal M5 receipt schema (v1) defined as required field lists.
Used by the validator to enforce presence of required keys.
"""

# Required top-level keys
REQUIRED_TOP_LEVEL = [
    "module",
    "gate_id",
    "decision",
    "actor",
    "inputs",
    "policy_snapshot_id",
    "timestamps",
    "signature",
]

# Nested requirements
REQUIRED_DECISION = ["outcome", "rationale"]
REQUIRED_ACTOR = ["type", "id", "client"]
REQUIRED_TIMESTAMPS = ["hw_monotonic_ms"]
REQUIRED_SIGNATURE = ["algo", "value"]

# Scalar (string) fields at top level
REQUIRED_STRING_FIELDS = ["module", "gate_id", "policy_snapshot_id"]

