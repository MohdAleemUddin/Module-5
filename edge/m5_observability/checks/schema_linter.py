from typing import Any, Dict, List


_RULE_UNKNOWN = "OBS-SCHEMA-0001"
_RULE_WRONG_TYPE = "OBS-SCHEMA-0002"
_ALLOWED_TYPES = {"str", "int", "float", "bool"}


def _validate_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(schema, dict):
        raise ValueError("Schema invalid: must be a dict")
    if "fields" not in schema:
        raise ValueError("Schema invalid: missing key fields")
    if "renames" not in schema:
        raise ValueError("Schema invalid: missing key renames")

    fields = schema["fields"]
    renames = schema["renames"]
    if not isinstance(fields, dict):
        raise ValueError("Schema invalid: fields must be a dict")
    if not isinstance(renames, dict):
        raise ValueError("Schema invalid: renames must be a dict")

    for name, spec in fields.items():
        if not isinstance(name, str) or not name:
            raise ValueError("Schema invalid: field names must be non-empty strings")
        if not isinstance(spec, dict):
            raise ValueError(f"Schema invalid: field spec for {name} must be a dict")
        if "type" not in spec:
            raise ValueError(f"Schema invalid: missing type for field {name}")
        field_type = spec["type"]
        if field_type not in _ALLOWED_TYPES:
            raise ValueError(f"Schema invalid: unsupported type for field {name}")

    for bad, good in renames.items():
        if not isinstance(bad, str) or not isinstance(good, str):
            raise ValueError("Schema invalid: renames must map strings to strings")
    return schema


def _type_matches(expected: str, value: Any) -> bool:
    if expected == "str":
        return isinstance(value, str)
    if expected == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "float":
        return isinstance(value, float)
    if expected == "bool":
        return isinstance(value, bool)
    return False


def _type_name(value: Any) -> str:
    return type(value).__name__


def lint_fields(payload: Dict[str, Any], schema: Dict[str, Any], kind: str) -> List[Dict[str, Any]]:
    if not isinstance(payload, dict):
        raise ValueError("Schema invalid: payload must be a dict")
    if kind not in {"log", "metric"}:
        raise ValueError("Schema invalid: kind must be log or metric")

    schema = _validate_schema(schema)
    fields = schema["fields"]
    renames = schema["renames"]

    violations: List[Dict[str, Any]] = []

    for field_name, value in sorted(payload.items(), key=lambda kv: kv[0]):
        if field_name not in fields:
            suggestion = (
                f"rename {field_name} -> {renames[field_name]}"
                if field_name in renames
                else "remove field or add to schema"
            )
            expected = renames.get(field_name, "schema field")
            violations.append(
                {
                    "rule_id": _RULE_UNKNOWN,
                    "field": field_name,
                    "issue": "unknown_field",
                    "expected": expected,
                    "actual": field_name,
                    "suggestion": suggestion,
                }
            )
            continue

        expected_type = fields[field_name]["type"]
        if not _type_matches(expected_type, value):
            violations.append(
                {
                    "rule_id": _RULE_WRONG_TYPE,
                    "field": field_name,
                    "issue": "wrong_type",
                    "expected": expected_type,
                    "actual": _type_name(value),
                    "suggestion": f"cast/normalize to {expected_type}",
                }
            )

    violations.sort(key=lambda v: (v["field"], v["rule_id"]))
    return violations

