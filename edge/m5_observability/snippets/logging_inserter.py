def plan_logging_insert(file_path: str, original_text: str, snippet_text: str, marker: str) -> dict:
    """
    Plan a logging snippet insertion.
    
    Args:
        file_path: Target file path
        original_text: Original file content
        snippet_text: Snippet to insert
        marker: Marker identifier
    
    Returns:
        dict with keys: file, patch, inverse_patch
    """
    start_marker = f"// <{marker}>"
    
    # Idempotent check: if marker already exists, return noop
    if start_marker in original_text:
        return {
            "file": file_path,
            "patch": {"op": "noop", "marker": marker},
            "inverse_patch": {"op": "noop", "marker": marker}
        }
    
    # Detect newline style
    newline = "\r\n" if "\r\n" in original_text else "\n"
    
    # Build insert block
    end_marker = f"// </{marker}>"
    insert_text = newline + start_marker + newline + snippet_text.strip() + newline + end_marker + newline
    
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
        PermissionError: If pc1_check denies the operation
    """
    if patch["op"] == "noop":
        return original_text
    
    # Call PC-1 check before making changes
    if not pc1_check(action="m5.log_snippet.insert", patch=patch):
        raise PermissionError("PC-1 denied m5.log_snippet.insert")
    
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
    if not pc1_check(action="m5.log_snippet.remove", patch=inverse_patch):
        raise PermissionError("PC-1 denied m5.log_snippet.remove")
    
    marker = inverse_patch["marker"]
    start_marker = f"// <{marker}>"
    end_marker = f"// </{marker}>"
    
    # Find and remove the first marker block
    start_idx = text.find(start_marker)
    if start_idx == -1:
        return text
    
    # Find the position to start removal (include leading newline if present)
    line_start = text.rfind('\n', 0, start_idx)
    if line_start == -1:
        line_start = 0
    # Don't add 1 - we want to include the newline that precedes the marker
    
    # Find end marker
    end_idx = text.find(end_marker, start_idx)
    if end_idx == -1:
        return text
    
    # Find the end of the line containing end_marker (include trailing newline if present)
    line_end = text.find('\n', end_idx)
    if line_end == -1:
        line_end = len(text)
    else:
        line_end += 1
    
    # Remove the block
    return text[:line_start] + text[line_end:]

