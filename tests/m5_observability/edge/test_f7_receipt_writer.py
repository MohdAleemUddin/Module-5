import json
import os

import pytest

from edge.m5_observability.receipts.writer import append_receipt_jsonl


def _valid_receipt():
    return {
        "module": "M5_observability_v1",
        "gate_id": "observability_gate_v1",
        "decision": {"outcome": "pass", "rationale": "ok"},
        "actor": {"type": "cli", "id": "user123", "client": "tests"},
        "inputs": {},
        "policy_snapshot_id": "snap-1",
        "timestamps": {"hw_monotonic_ms": 0},
        "signature": {"algo": "stub-sha256", "value": "stub"},
    }


def test_append_only_writes_two_lines(tmp_path):
    path = tmp_path / "receipts.jsonl"
    a = _valid_receipt()
    b = _valid_receipt()
    b["decision"] = {"outcome": "warn", "rationale": "low cov"}

    append_receipt_jsonl(str(path), a)
    append_receipt_jsonl(str(path), b)

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert lines[0] == json.dumps(a, separators=(",", ":"), sort_keys=True)
    assert lines[1] == json.dumps(b, separators=(",", ":"), sort_keys=True)


def test_stable_ordering(tmp_path):
    path = tmp_path / "receipts.jsonl"
    receipt = _valid_receipt()
    append_receipt_jsonl(str(path), receipt)

    line = path.read_text(encoding="utf-8").strip()
    assert line == json.dumps(receipt, separators=(",", ":"), sort_keys=True)


def test_fsync_false(tmp_path):
    path = tmp_path / "receipts.jsonl"
    receipt = _valid_receipt()
    append_receipt_jsonl(str(path), receipt, fsync=False)

    assert path.exists()
    assert path.read_text(encoding="utf-8").strip()


def test_validation_enforced(tmp_path):
    path = tmp_path / "receipts.jsonl"
    bad = _valid_receipt()
    bad.pop("policy_snapshot_id")

    with pytest.raises(ValueError):
        append_receipt_jsonl(str(path), bad)

    assert not path.exists() or path.read_text(encoding="utf-8") == ""


