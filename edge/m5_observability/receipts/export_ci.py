"""
Privacy-safe export of receipts for CI artifacts.
Sanitizes sensitive strings and dynamic keys before writing JSONL.
"""

import hashlib
import json
import re
from typing import Any, Dict


_EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_AUTH_BEARER_RE = re.compile(r"\bauthorization\b.*\bbearer\b", re.IGNORECASE)
_TOKEN_RE = re.compile(r"\b(token|api[_-]?key|secret)\b\s*[:=]", re.IGNORECASE)

_RAW_VALUE_KEYS = {"match", "raw", "value"}


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _is_sensitive_string(s: str) -> bool:
    return bool(
        _EMAIL_RE.search(s)
        or _AUTH_BEARER_RE.search(s)
        or _TOKEN_RE.search(s)
    )


def _should_hash_key(key: str) -> bool:
    return ("{" in key) or ("}" in key) or ("${" in key) or bool(_EMAIL_RE.search(key))


def _sanitize(obj: Any) -> Any:
    if isinstance(obj, str):
        return f"h:{_hash(obj)}" if _is_sensitive_string(obj) else obj

    if isinstance(obj, list):
        return [_sanitize(item) for item in obj]

    if isinstance(obj, dict):
        sanitized: Dict[str, Any] = {}
        for k, v in obj.items():
            new_key = f"hk:{_hash(k)}" if isinstance(k, str) and _should_hash_key(k) else k

            if isinstance(v, str) and isinstance(k, str) and k in _RAW_VALUE_KEYS:
                sanitized_value = f"h:{_hash(v)}"
            else:
                sanitized_value = _sanitize(v)

            sanitized[new_key] = sanitized_value
        return sanitized

    return obj


def export_privacy_safe_jsonl(in_path: str, out_path: str) -> None:
    with open(in_path, "r", encoding="utf-8") as fin, open(
        out_path, "w", encoding="utf-8", newline="\n"
    ) as fout:
        for line in fin:
            if not line.strip():
                continue
            data = json.loads(line)
            sanitized = _sanitize(data)
            fout.write(json.dumps(sanitized, separators=(",", ":"), sort_keys=True))
            fout.write("\n")


