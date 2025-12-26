import json
from collections import OrderedDict

import pytest

from edge.m5_observability.policy.loader import load_observability_policy


def test_loads_valid_policy(tmp_path):
    policy_file = tmp_path / "policy.json"
    data = {
        "module": "observability",
        "version": "1.0",
        "gate_mode": "Warn",
        "policy": {
            "obs.required_signals": ["cpu.util", "mem.util"],
            "obs.min_telemetry_coverage_warn": 0.7,
            "obs.min_telemetry_coverage_block": 0.9,
            "obs.require_correlation_id": True,
            "obs.require_hw_timestamp": True,
            "obs.max_label_cardinality_warn": 10,
            "obs.max_label_cardinality_block": 20,
            "obs.disallow_dynamic_keys": False,
        },
    }
    policy_file.write_text(json.dumps(data), encoding="utf-8")

    result = load_observability_policy(str(policy_file))

    expected = OrderedDict(
        [
            ("obs.required_signals", ["cpu.util", "mem.util"]),
            ("obs.min_telemetry_coverage_warn", 0.7),
            ("obs.min_telemetry_coverage_block", 0.9),
            ("obs.require_correlation_id", True),
            ("obs.require_hw_timestamp", True),
            ("obs.max_label_cardinality_warn", 10),
            ("obs.max_label_cardinality_block", 20),
            ("obs.disallow_dynamic_keys", False),
            ("gate_mode", "Warn"),
        ]
    )
    assert result == expected
    assert list(result.keys()) == [
        "obs.required_signals",
        "obs.min_telemetry_coverage_warn",
        "obs.min_telemetry_coverage_block",
        "obs.require_correlation_id",
        "obs.require_hw_timestamp",
        "obs.max_label_cardinality_warn",
        "obs.max_label_cardinality_block",
        "obs.disallow_dynamic_keys",
        "gate_mode",
    ]


def test_missing_key_raises(tmp_path):
    policy_file = tmp_path / "policy.json"
    data = {
        "module": "observability",
        "version": "1.0",
        "policy": {
            "obs.required_signals": ["cpu.util"],
            "obs.min_telemetry_coverage_warn": 0.5,
            "obs.min_telemetry_coverage_block": 0.8,
            "obs.require_correlation_id": True,
            # missing obs.require_hw_timestamp
            "obs.max_label_cardinality_warn": 5,
            "obs.max_label_cardinality_block": 6,
            "obs.disallow_dynamic_keys": True,
            "gate_mode": "Soft",
        },
    }
    policy_file.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError) as excinfo:
        load_observability_policy(str(policy_file))

    assert "obs.require_hw_timestamp" in str(excinfo.value)


def test_invalid_json_raises(tmp_path):
    policy_file = tmp_path / "policy.json"
    policy_file.write_text('{"module": "observability", "version": "1.0", ', encoding="utf-8")

    with pytest.raises(ValueError) as excinfo:
        load_observability_policy(str(policy_file))

    message = str(excinfo.value)
    assert "invalid JSON" in message or "unreadable" in message

