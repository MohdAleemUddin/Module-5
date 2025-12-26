import json
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict

_ALLOWED_GATE_MODES = {"Off", "Warn", "Soft", "Hard"}
_ORDERED_KEYS = [
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


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _require_key(container: Dict[str, Any], key: str) -> Any:
    if key not in container:
        raise ValueError(f"Policy invalid: missing key {key}")
    return container[key]


def load_observability_policy(policy_path: str) -> Dict[str, Any]:
    """Load and validate an observability policy JSON bundle."""
    path = Path(policy_path)
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except FileNotFoundError as exc:
        raise ValueError("Policy unreadable: file not found") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Policy invalid JSON: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"Policy unreadable: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Policy invalid: top-level JSON must be an object")

    module = _require_key(data, "module")
    version = _require_key(data, "version")
    policy = _require_key(data, "policy")

    if not isinstance(module, str) or not module:
        raise ValueError("Policy invalid: module must be a non-empty string")
    if not isinstance(version, str) or not version:
        raise ValueError("Policy invalid: version must be a non-empty string")
    if not isinstance(policy, dict):
        raise ValueError("Policy invalid: policy must be an object")

    gate_mode = data.get("gate_mode", policy.get("gate_mode"))
    if gate_mode is None:
        raise ValueError("Policy invalid: missing key gate_mode")
    if gate_mode not in _ALLOWED_GATE_MODES:
        raise ValueError("Policy invalid: gate_mode must be one of Off, Warn, Soft, Hard")

    required_signals = _require_key(policy, "obs.required_signals")
    if not isinstance(required_signals, list) or not required_signals:
        raise ValueError("Policy invalid: obs.required_signals must be a non-empty list of strings")
    for signal in required_signals:
        if not isinstance(signal, str) or not signal:
            raise ValueError("Policy invalid: obs.required_signals must contain non-empty strings")

    coverage_warn = _require_key(policy, "obs.min_telemetry_coverage_warn")
    coverage_block = _require_key(policy, "obs.min_telemetry_coverage_block")
    if not _is_number(coverage_warn) or not 0.0 <= float(coverage_warn) <= 1.0:
        raise ValueError("Policy invalid: obs.min_telemetry_coverage_warn must be a number between 0.0 and 1.0")
    if not _is_number(coverage_block) or not 0.0 <= float(coverage_block) <= 1.0:
        raise ValueError("Policy invalid: obs.min_telemetry_coverage_block must be a number between 0.0 and 1.0")

    require_corr = _require_key(policy, "obs.require_correlation_id")
    if not isinstance(require_corr, bool):
        raise ValueError("Policy invalid: obs.require_correlation_id must be a bool")

    require_hw = _require_key(policy, "obs.require_hw_timestamp")
    if not isinstance(require_hw, bool):
        raise ValueError("Policy invalid: obs.require_hw_timestamp must be a bool")

    max_card_warn = _require_key(policy, "obs.max_label_cardinality_warn")
    max_card_block = _require_key(policy, "obs.max_label_cardinality_block")
    if not isinstance(max_card_warn, int) or isinstance(max_card_warn, bool) or max_card_warn < 0:
        raise ValueError("Policy invalid: obs.max_label_cardinality_warn must be an int >= 0")
    if not isinstance(max_card_block, int) or isinstance(max_card_block, bool) or max_card_block < 0:
        raise ValueError("Policy invalid: obs.max_label_cardinality_block must be an int >= 0")
    if max_card_block < max_card_warn:
        raise ValueError("Policy invalid: obs.max_label_cardinality_block must be >= obs.max_label_cardinality_warn")

    disallow_dynamic = _require_key(policy, "obs.disallow_dynamic_keys")
    if not isinstance(disallow_dynamic, bool):
        raise ValueError("Policy invalid: obs.disallow_dynamic_keys must be a bool")

    ordered_policy = OrderedDict()
    ordered_policy["obs.required_signals"] = required_signals
    ordered_policy["obs.min_telemetry_coverage_warn"] = float(coverage_warn)
    ordered_policy["obs.min_telemetry_coverage_block"] = float(coverage_block)
    ordered_policy["obs.require_correlation_id"] = require_corr
    ordered_policy["obs.require_hw_timestamp"] = require_hw
    ordered_policy["obs.max_label_cardinality_warn"] = max_card_warn
    ordered_policy["obs.max_label_cardinality_block"] = max_card_block
    ordered_policy["obs.disallow_dynamic_keys"] = disallow_dynamic
    ordered_policy["gate_mode"] = gate_mode

    return ordered_policy

