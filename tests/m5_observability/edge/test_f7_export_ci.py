import hashlib
import json

from edge.m5_observability.receipts.export_ci import export_privacy_safe_jsonl


def _h(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def test_export_sanitizes_sensitive_data(tmp_path):
    in_path = tmp_path / "in.jsonl"
    out_path = tmp_path / "out.jsonl"

    receipt = {
        "pii_findings": [
            {"rule_id": "PII-EMAIL", "file": "a", "line": 1, "match": "test@example.com"},
            {"rule_id": "PII-AUTH", "file": "a", "line": 2, "match": "Authorization: Bearer abc"},
        ],
        "dynamic": {"owners.{userId}": "x"},
        "note": "token=abcd1234",
    }

    in_path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")

    export_privacy_safe_jsonl(str(in_path), str(out_path))

    out_text = out_path.read_text(encoding="utf-8")

    # Raw sensitive data should be absent
    assert "test@example.com" not in out_text
    assert "Bearer abc" not in out_text
    assert "owners.{userId}" not in out_text
    assert "token=abcd1234" not in out_text

    # Hashes should be present
    assert _h("test@example.com") in out_text
    assert _h("Authorization: Bearer abc") in out_text
    assert _h("owners.{userId}") in out_text
    assert _h("token=abcd1234") in out_text

    # Single line, stable ordering via sort_keys
    lines = out_text.splitlines()
    assert len(lines) == 1
    sanitized = json.loads(lines[0])
    # Check hashed key is present
    hashed_key = f"hk:{_h('owners.{userId}')}"
    assert hashed_key in sanitized["dynamic"]


