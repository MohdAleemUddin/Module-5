import pytest

from edge.m5_observability.checks.schema_linter import lint_fields


def _base_schema():
    return {
        "fields": {
            "request_id": {"type": "str"},
        },
        "renames": {"req_id": "request_id"},
    }


def test_unknown_field_with_rename():
    schema = _base_schema()
    payload = {"req_id": "abc"}

    violations = lint_fields(payload, schema, kind="log")

    assert len(violations) == 1
    v = violations[0]
    assert v["rule_id"] == "OBS-SCHEMA-0001"
    assert v["issue"] == "unknown_field"
    assert "rename req_id -> request_id" in v["suggestion"]
    assert v["expected"] == "request_id"
    assert v["actual"] == "req_id"


def test_wrong_type_detected():
    schema = _base_schema()
    payload = {"request_id": 123}

    violations = lint_fields(payload, schema, kind="metric")

    assert len(violations) == 1
    v = violations[0]
    assert v["rule_id"] == "OBS-SCHEMA-0002"
    assert v["issue"] == "wrong_type"
    assert v["expected"] == "str"
    assert v["actual"] == "int"
    assert "cast/normalize to str" in v["suggestion"]


def test_deterministic_sorting():
    schema = _base_schema()
    payload = {
        "z_field": 1,
        "request_id": True,  # wrong type
        "a_field": "ok",
    }

    violations = lint_fields(payload, schema, kind="log")

    assert [v["field"] for v in violations] == ["a_field", "request_id", "z_field"]
    assert [v["rule_id"] for v in violations] == [
        "OBS-SCHEMA-0001",
        "OBS-SCHEMA-0002",
        "OBS-SCHEMA-0001",
    ]

