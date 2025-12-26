import json
from pathlib import Path

from edge.m5_observability.checks.pii_redaction import build_redaction_plan


def _apply_plan(text: str, plan):
    redacted = text
    for item in sorted(plan, key=lambda i: i["start"], reverse=True):
        redacted = redacted[: item["start"]] + item["replacement"] + redacted[item["end"] :]
    return redacted


def test_build_plan_and_mapping(tmp_path):
    text = (
        "Authorization: Bearer abc123\n"
        "email=user@example.com\n"
        "token=tok_456\n"
    )
    rules = [
        {"rule_id": "PII-001", "pattern": r"Authorization:\s*Bearer\s+\S+"},
        {"rule_id": "PII-002", "pattern": r"email=\S+"},
        {"rule_id": "PII-003", "pattern": r"token=\S+"},
    ]

    plan_result = build_redaction_plan(text, rules, mode="hash")
    plan = plan_result["plan"]

    assert len(plan) == 3
    assert plan == sorted(plan, key=lambda i: (i["start"], i["end"], i["rule_id"], i["replacement"]))

    redacted = _apply_plan(text, plan)
    assert "<REDACTED:sha256:" in redacted

    mapping_file = tmp_path / "m5_pii_redaction_map.json"
    receipt_file = tmp_path / "receipts_m5.jsonl"

    mapping_entries = []
    for item in plan:
        original = text[item["start"] : item["end"]]
        mapping_entries.append(
            {
                "file": "file://test.txt",
                "rule_id": item["rule_id"],
                "start": item["start"],
                "end": item["end"],
                "original": original,
                "replacement": item["replacement"],
            }
        )

    mapping_file.write_text("\n".join(json.dumps(e) for e in mapping_entries) + "\n", encoding="utf-8")
    receipt_entry = {
        "module": "M5_observability_v1",
        "action": "pii_redaction",
        "pc1_attested": True,
        "redactions_applied": [
            {
                "file": "file://test.txt",
                "rule_id": item["rule_id"],
                "start": item["start"],
                "end": item["end"],
                "replacement": item["replacement"],
            }
            for item in plan
        ],
        "mapping_file": "m5_pii_redaction_map.json",
    }
    receipt_file.write_text(json.dumps(receipt_entry) + "\n", encoding="utf-8")

    mapping_content = mapping_file.read_text(encoding="utf-8")
    assert "Authorization: Bearer abc123" in mapping_content
    assert "user@example.com" in mapping_content
    assert "tok_456" in mapping_content

    receipt_content = receipt_file.read_text(encoding="utf-8")
    assert "Authorization: Bearer" not in receipt_content
    assert "user@example.com" not in receipt_content
    assert "tok_456" not in receipt_content
    assert "PII-001" in receipt_content
    assert "mapping_file" in receipt_content


def test_deterministic_plan():
    text = "token=abc token=abc"
    rules = [{"rule_id": "PII-003", "pattern": r"token=\S+"}]

    first = build_redaction_plan(text, rules, mode="hash")["plan"]
    second = build_redaction_plan(text, rules, mode="hash")["plan"]

    assert first == second

