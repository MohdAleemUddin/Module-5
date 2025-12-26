def validate_label_keys(label_keys: list[str], disallow_dynamic_keys: bool = True) -> tuple[bool, list[str]]:
    """
    Validate label keys for dynamic/unsafe patterns.
    
    Args:
        label_keys: List of label key strings
        disallow_dynamic_keys: Whether to disallow dynamic patterns
    
    Returns:
        Tuple of (is_valid, sorted_invalid_keys)
    """
    if not disallow_dynamic_keys:
        return (True, [])
    
    unsafe_chars = {"${", "{", "}", "[", "]", "(", ")", " ", ":"}
    invalid_keys = []
    
    for key in label_keys:
        for unsafe in unsafe_chars:
            if unsafe in key:
                invalid_keys.append(key)
                break
    
    if invalid_keys:
        return (False, sorted(list(set(invalid_keys))))
    
    return (True, [])


def plan_metrics_insert(file_path: str, original_text: str, policy_cfg: dict, label_keys: list[str], marker: str) -> dict:
    """
    Plan a metrics snippet insertion with policy enforcement.
    
    Args:
        file_path: Target file path
        original_text: Original file content
        policy_cfg: Policy configuration dict
        label_keys: List of label keys
        marker: Marker identifier
    
    Returns:
        dict with keys: file, patch, inverse_patch
    
    Raises:
        ValueError: If policy_cfg missing required keys
    """
    # Validate policy config
    required_keys = ["obs.sample_rate_default", "obs.disallow_dynamic_keys"]
    for key in required_keys:
        if key not in policy_cfg:
            raise ValueError(f"Missing required policy key: {key}")
    
    start_line = f"// <{marker}>"
    end_line = f"// </{marker}>"
    
    # Idempotent check
    if start_line in original_text:
        return {
            "file": file_path,
            "patch": {"op": "noop", "marker": marker},
            "inverse_patch": {"op": "noop", "marker": marker}
        }
    
    # Normalize label keys: sorted unique
    normalized_keys = sorted(list(set(label_keys)))
    
    # Validate label keys
    disallow_dynamic = policy_cfg["obs.disallow_dynamic_keys"]
    is_valid, invalid_keys = validate_label_keys(normalized_keys, disallow_dynamic)
    
    if not is_valid:
        reason = f"Dynamic keys not allowed: {', '.join(invalid_keys)}"
        return {
            "file": file_path,
            "patch": {"op": "blocked", "marker": marker, "reason": reason},
            "inverse_patch": {"op": "noop", "marker": marker}
        }
    
    # Detect newline style
    newline = "\r\n" if "\r\n" in original_text else "\n"
    
    # Get sample rate
    sample_rate = policy_cfg["obs.sample_rate_default"]
    
    # Build snippet text
    labels_str = ",".join(normalized_keys)
    snippet_lines = [
        start_line,
        f"// sample_rate={sample_rate}",
        f"// labels=[{labels_str}]",
        "// counter:<name>",
        "// histogram:<name>",
        "// timer:<name>",
        end_line
    ]
    
    insert_text = newline + newline.join(snippet_lines) + newline
    
    return {
        "file": file_path,
        "patch": {
            "op": "insert_block",
            "marker": marker,
            "insert_at": "eof",
            "text": insert_text
        },
        "inverse_patch": {
            "op": "remove_block",
            "marker": marker
        }
    }


def apply_patch(original_text: str, patch: dict, pc1_check) -> str:
    """
    Apply a patch with PC-1 permission check.
    
    Args:
        original_text: Original text
        patch: Patch dictionary
        pc1_check: Permission check callable
    
    Returns:
        Modified text
    
    Raises:
        ValueError: If patch is blocked
        PermissionError: If pc1_check denies the operation
    """
    if patch["op"] == "noop":
        return original_text
    
    if patch["op"] == "blocked":
        raise ValueError(patch["reason"])
    
    # Call PC-1 check before making changes
    if not pc1_check(action="m5.metrics_snippet.insert", patch=patch):
        raise PermissionError("PC-1 denied m5.metrics_snippet.insert")
    
    # Apply patch by appending to EOF
    return original_text + patch["text"]


def apply_inverse(text: str, inverse_patch: dict, pc1_check) -> str:
    """
    Apply inverse patch to remove a marker block.
    
    Args:
        text: Current text
        inverse_patch: Inverse patch dictionary
        pc1_check: Permission check callable
    
    Returns:
        Modified text
    
    Raises:
        PermissionError: If pc1_check denies the operation
    """
    if inverse_patch["op"] == "noop":
        return text
    
    # Call PC-1 check before making changes
    if not pc1_check(action="m5.metrics_snippet.remove", patch=inverse_patch):
        raise PermissionError("PC-1 denied m5.metrics_snippet.remove")
    
    marker = inverse_patch["marker"]
    start_marker = f"// <{marker}>"
    end_marker = f"// </{marker}>"
    
    # Find and remove the first marker block
    start_idx = text.find(start_marker)
    if start_idx == -1:
        return text
    
    # Find end marker
    end_idx = text.find(end_marker, start_idx)
    if end_idx == -1:
        return text
    
    # Detect newline style
    newline = "\r\n" if "\r\n" in text else "\n"
    newline_len = len(newline)
    
    # Find start position (include leading newline before start_marker)
    line_start = start_idx
    # Check if there's a newline right before start_marker
    if start_idx >= newline_len and text[start_idx-newline_len:start_idx] == newline:
        line_start = start_idx - newline_len
    
    # Find end position (include trailing newline after end_marker)
    line_end = end_idx + len(end_marker)
    # Check if there's a newline right after end_marker
    if line_end < len(text) and text[line_end:line_end+newline_len] == newline:
        line_end += newline_len
    
    # Remove the block
    return text[:line_start] + text[line_end:]

