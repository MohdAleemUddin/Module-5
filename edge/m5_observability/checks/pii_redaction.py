import hashlib
import json
import re
from typing import Any, Dict, List


def _hash_value(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"<REDACTED:sha256:{digest}>"


def _build_replacement(value: str, mode: str) -> str:
    if mode == "hash":
        return _hash_value(value)
    if mode == "drop":
        return "<DROPPED>"
    raise ValueError("Invalid mode; must be hash or drop")


def build_redaction_plan(text: str, rules: List[Dict[str, Any]], mode: str) -> Dict[str, Any]:
    if mode not in {"hash", "drop"}:
        raise ValueError("Invalid mode; must be hash or drop")

    plan: List[Dict[str, Any]] = []
    for rule in rules:
        rule_id = rule.get("rule_id")
        pattern = rule.get("pattern")
        if not isinstance(rule_id, str) or not isinstance(pattern, str):
            raise ValueError("Invalid rule; requires rule_id and pattern strings")
        for match in re.finditer(pattern, text):
            replacement = _build_replacement(match.group(0), mode)
            plan.append(
                {
                    "rule_id": rule_id,
                    "start": match.start(),
                    "end": match.end(),
                    "replacement": replacement,
                }
            )

    plan.sort(key=lambda item: (item["start"], item["end"], item["rule_id"], item["replacement"]))
    return {"mode": mode, "plan": plan}

