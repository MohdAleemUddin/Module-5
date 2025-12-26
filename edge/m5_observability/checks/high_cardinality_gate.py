from typing import Dict

_RULE_ID = "OBS-CARD-0001"
_VALID_OUTCOMES = {"hard_block", "soft_block"}


def _validate_inputs(cardinality: int, warn: int, block: int, block_outcome: str) -> None:
    for name, value in (("cardinality", cardinality), ("warn", warn), ("block", block)):
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"Invalid input: {name} must be int")
        if value < 0:
            raise ValueError(f"Invalid input: {name} must be >= 0")
    if block < warn:
        raise ValueError("Invalid input: block must be >= warn")
    if block_outcome not in _VALID_OUTCOMES:
        raise ValueError("Invalid input: block_outcome must be hard_block or soft_block")


def eval_label_cardinality(cardinality: int, warn: int, block: int, block_outcome: str = "hard_block") -> Dict[str, str]:
    _validate_inputs(cardinality, warn, block, block_outcome)

    if cardinality > block:
        outcome = block_outcome
    elif cardinality > warn:
        outcome = "warn"
    else:
        outcome = "pass"

    rationale = (
        f"CARD: cardinality={cardinality}, warn={warn}, block={block}, outcome={outcome}"
    )

    return {"outcome": outcome, "rule_id": _RULE_ID, "rationale": rationale}

