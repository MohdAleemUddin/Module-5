import json
import sys

from edge.m5_observability.checks.pii_redaction import build_redaction_plan


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
        text = payload["text"]
        rules = payload["rules"]
        mode = payload["mode"]
        result = build_redaction_plan(text, rules, mode)
        sys.stdout.write(json.dumps(result))
        return 0
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        sys.stderr.write(str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())

