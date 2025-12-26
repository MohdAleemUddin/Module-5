def add_m1_linkage(receipt: dict, telemetry_coverage_pct: float, roi_tags: list[str]) -> dict:
    """
    Add M1 Guard-Window synergy linkage to receipt.
    
    Args:
        receipt: Receipt dictionary to modify
        telemetry_coverage_pct: Telemetry coverage percentage
        roi_tags: List of ROI tags
    
    Returns:
        Modified receipt dictionary
    """
    # Ensure inputs dict exists
    if "inputs" not in receipt:
        receipt["inputs"] = {}
    
    # Set telemetry coverage
    receipt["inputs"]["telemetry_coverage_pct"] = telemetry_coverage_pct
    
    # Set ROI tags
    receipt["roi_tags"] = roi_tags
    
    return receipt

