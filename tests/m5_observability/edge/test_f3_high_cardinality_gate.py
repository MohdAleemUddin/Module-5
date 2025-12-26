import pytest

from edge.m5_observability.checks.high_cardinality_gate import eval_label_cardinality


def test_warn_when_above_warn_below_block():
    result = eval_label_cardinality(200, warn=100, block=500)
    assert result["outcome"] == "warn"
    assert result["rule_id"] == "OBS-CARD-0001"
    assert "cardinality=200" in result["rationale"]


def test_block_when_above_block_hard_and_soft():
    hard = eval_label_cardinality(600, warn=100, block=500, block_outcome="hard_block")
    soft = eval_label_cardinality(600, warn=100, block=500, block_outcome="soft_block")

    assert hard["outcome"] == "hard_block"
    assert soft["outcome"] == "soft_block"
    assert "cardinality=600" in hard["rationale"]
    assert "cardinality=600" in soft["rationale"]


def test_boundaries():
    at_warn = eval_label_cardinality(100, warn=100, block=500)
    at_block = eval_label_cardinality(500, warn=100, block=500)

    assert at_warn["outcome"] == "pass"
    assert at_block["outcome"] == "warn"


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        eval_label_cardinality(-1, warn=0, block=1)
    with pytest.raises(ValueError):
        eval_label_cardinality(1, warn=5, block=4)
    with pytest.raises(ValueError):
        eval_label_cardinality(1, warn=0, block=1, block_outcome="maybe")

