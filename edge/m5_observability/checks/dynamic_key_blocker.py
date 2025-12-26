import re
from typing import Any, Dict, List

_RULE_ID = "OBS-DYNKEY-0001"
_INDICATORS = ("labels[", "labels.", "label_", "tags[")


def _parse_hunk_header(header: str) -> int:
    # Header format: @@ -a,b +c,d @@
    try:
        plus_part = header.split("+", 1)[1]
        new_section = plus_part.split(" ", 1)[0]
        start = new_section.split(",")[0]
        return int(start)
    except Exception as exc:
        raise ValueError(f"Invalid diff hunk header: {header}") from exc


def _extract_placeholder(text: str) -> str:
    match = re.search(r"\{([^{}]+)\}", text)
    if not match:
        return ""
    return match.group(1)


def _suggest_rewrite(line: str) -> Dict[str, str]:
    placeholder = _extract_placeholder(line).lower()
    base = "user" if "user" in line.lower() else (placeholder or "id")
    if not base.endswith("_id"):
        base = f"{base}_id"

    if "tags[" in line:
        prefix = "tags"
    else:
        prefix = "labels"

    static_key = f"{prefix}[{base}]"
    return {"static_key": static_key, "value_field": base}


def find_dynamic_keys(unified_diff: str) -> List[Dict[str, Any]]:
    current_file = None
    new_line_no = None
    in_hunk = False
    violations: List[Dict[str, Any]] = []

    for raw_line in unified_diff.splitlines():
        if raw_line.startswith("+++ "):
            # Format: +++ b/path
            parts = raw_line.split(" ", 2)
            if len(parts) >= 2 and parts[1].startswith("b/"):
                current_file = parts[1][2:]
            else:
                current_file = parts[-1] if len(parts) >= 2 else None
            continue

        if raw_line.startswith("@@"):
            new_line_no = _parse_hunk_header(raw_line)
            in_hunk = True
            continue

        if not in_hunk or current_file is None or new_line_no is None:
            continue

        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            content = raw_line[1:]
            # Check only added lines
            if any(ind in content for ind in _INDICATORS) and (
                "${" in content or ("{" in content and "}" in content)
            ):
                snippet = content.strip()
                suggestion = _suggest_rewrite(content)
                violations.append(
                    {
                        "file": current_file,
                        "line": new_line_no,
                        "snippet": snippet,
                        "suggested_rewrite": suggestion,
                    }
                )
            new_line_no += 1
        elif raw_line.startswith(" "):
            new_line_no += 1
        # '-' lines only advance old file count, so skip increment

    violations.sort(key=lambda v: (v["file"], v["line"], v["snippet"]))
    return violations


def eval_dynamic_keys(unified_diff: str, disallow_dynamic_keys: bool) -> Dict[str, Any]:
    violations = find_dynamic_keys(unified_diff)
    outcome = "pass"
    if disallow_dynamic_keys and violations:
        outcome = "hard_block"

    rationale = f"DYNKEY: count={len(violations)}"

    return {
        "disallow_dynamic_keys": disallow_dynamic_keys,
        "violations": violations,
        "outcome": outcome,
        "rule_id": _RULE_ID,
        "rationale": rationale,
    }

