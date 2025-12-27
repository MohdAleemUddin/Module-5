def has_correlation_helper(text: str) -> bool:
    """
    Check if correlation helper is already present.
    
    Args:
        text: Text to check
    
    Returns:
        True if all required tokens are present
    """
    required_tokens = ["request_id", "trace_id", "getCorrelationIds"]
    return all(token in text for token in required_tokens)


def plan_correlation_inject(file_path: str, original_text: str, policy_cfg: dict, marker: str) -> dict:
    """
    Plan a correlation ID helper injection.
    
    Args:
        file_path: Target file path
        original_text: Original file content
        policy_cfg: Policy configuration dict
        marker: Marker identifier
    
    Returns:
        dict with keys: file, patch, inverse_patch
    """
    # Check policy requirement
    if not policy_cfg.get("obs.require_correlation_id", False):
        return {
            "file": file_path,
            "patch": {"op": "noop", "marker": marker},
            "inverse_patch": {"op": "noop", "marker": marker}
        }
    
    # Check if helper already exists
    if has_correlation_helper(original_text):
        return {
            "file": file_path,
            "patch": {"op": "noop", "marker": marker},
            "inverse_patch": {"op": "noop", "marker": marker}
        }
    
    # Detect newline style
    newline = "\r\n" if "\r\n" in original_text else "\n"
    
    # Build minimal helper stub
    start_line = f"// <{marker}>"
    end_line = f"// </{marker}>"
    
    stub_content = 'function getCorrelationIds(input: any): { request_id: string; trace_id: string } {\n    // Extract correlation IDs from request headers or generate new ones\n    const request_id = input?.headers?.[\'x-request-id\'] || input?.request_id || generateId();\n    const trace_id = input?.headers?.[\'x-trace-id\'] || input?.trace_id || generateId();\n    return { request_id, trace_id };\n}\n\nfunction generateId(): string {\n    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);\n}'
    
    insert_text = newline + start_line + newline + stub_content + newline + end_line + newline
    
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
    if not pc1_check(action="m5.correlation.inject", patch=patch):
        raise PermissionError("PC-1 denied m5.correlation.inject")
    
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
    if not pc1_check(action="m5.correlation.remove", patch=inverse_patch):
        raise PermissionError("PC-1 denied m5.correlation.remove")
    
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

