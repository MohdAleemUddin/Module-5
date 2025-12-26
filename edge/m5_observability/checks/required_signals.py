def check_required_signals(surface_text: str, required_signals: list[str]) -> dict:
    """
    Check which required signals are present or missing in surface_text.
    
    Args:
        surface_text: Text to search for signals
        required_signals: List of signal tokens to check
    
    Returns:
        Dict with keys: signals_present, signals_missing (both sorted unique lists)
    """
    unique_signals = set(required_signals)
    present = set()
    
    for signal in unique_signals:
        if signal in surface_text:
            present.add(signal)
    
    missing = unique_signals - present
    
    return {
        "signals_present": sorted(list(present)),
        "signals_missing": sorted(list(missing))
    }

