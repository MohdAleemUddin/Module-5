from edge.m5_observability.checks.dynamic_key_blocker import (
    eval_dynamic_keys,
    find_dynamic_keys,
)


def _diff_with_content(content: str) -> str:
    return (
        "diff --git a/src/x.ts b/src/x.ts\n"
        "--- a/src/x.ts\n"
        "+++ b/src/x.ts\n"
        "@@ -0,0 +1,3 @@\n"
        "+// added\n"
        f"+{content}\n"
        "+// end\n"
    )


def test_detect_dynamic_key_with_suggestion():
    diff = _diff_with_content("labels[user.${id}] = 1")

    violations = find_dynamic_keys(diff)

    assert len(violations) == 1
    v = violations[0]
    assert v["file"] == "src/x.ts"
    assert "labels[user.${id}]" in v["snippet"]
    assert v["suggested_rewrite"]["static_key"] == "labels[user_id]"
    assert v["suggested_rewrite"]["value_field"] == "user_id"


def test_disallow_true_blocks():
    diff = _diff_with_content("labels[user.${id}] = 1")

    result = eval_dynamic_keys(diff, disallow_dynamic_keys=True)

    assert result["outcome"] == "hard_block"
    assert len(result["violations"]) == 1


def test_disallow_false_passes_but_reports():
    diff = _diff_with_content("labels[user.${id}] = 1")

    result = eval_dynamic_keys(diff, disallow_dynamic_keys=False)

    assert result["outcome"] == "pass"
    assert len(result["violations"]) == 1


def test_deterministic_output():
    diff = _diff_with_content("labels[user.${id}] = 1")

    first = find_dynamic_keys(diff)
    second = find_dynamic_keys(diff)

    assert first == second

