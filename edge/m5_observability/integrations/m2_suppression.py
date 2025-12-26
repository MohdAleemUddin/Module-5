def apply_m2_conflict_hot_suppression(
    files_touched: list[str],
    m2_outcome: str,
    m2_conflict_files: list[str]
) -> dict:
    """
    Apply M2 conflict-hot suppression logic.
    
    Args:
        files_touched: List of files being touched by current operation
        m2_outcome: M2 merge conflict detection outcome
        m2_conflict_files: List of files with M2 conflicts
    
    Returns:
        dict with keys: execution_mode, writes_allowed, suppressed
    """
    # Normalize paths (lowercase, replace backslash with forward slash)
    def normalize_path(path: str) -> str:
        return path.lower().replace("\\", "/")
    
    normalized_touched = {normalize_path(f) for f in files_touched}
    normalized_conflicts = {normalize_path(f) for f in m2_conflict_files}
    
    # Check for overlap
    has_overlap = bool(normalized_touched & normalized_conflicts)
    
    # Determine suppression
    hot_outcomes = {"warn", "soft_block", "hard_block"}
    
    if m2_outcome in hot_outcomes and has_overlap:
        return {
            "execution_mode": "explain_only",
            "writes_allowed": False,
            "suppressed": True
        }
    else:
        return {
            "execution_mode": "normal",
            "writes_allowed": True,
            "suppressed": False
        }


def apply_suppression_to_receipt(receipt: dict, suppression: dict) -> dict:
    """
    Apply suppression settings to a receipt.
    
    Args:
        receipt: Receipt dictionary to modify
        suppression: Suppression settings from apply_m2_conflict_hot_suppression
    
    Returns:
        Modified receipt dictionary
    """
    # Set execution_mode
    receipt["execution_mode"] = suppression["execution_mode"]
    
    # Ensure actions dict exists
    if "actions" not in receipt:
        receipt["actions"] = {}
    
    # Set writes_allowed
    receipt["actions"]["writes_allowed"] = suppression["writes_allowed"]
    
    return receipt

