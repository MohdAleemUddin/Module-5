def compute_coverage(present: list[str], required: list[str]) -> float:
    """
    Compute coverage as the ratio of present items that are in required.
    
    Args:
        present: List of present items
        required: List of required items
    
    Returns:
        Coverage ratio (0.0 to 1.0), rounded to 2 decimal places
    """
    R = set(required)
    if not R:
        return 0.0
    
    P = set(present)
    intersection = P & R
    coverage = len(intersection) / len(R)
    return round(coverage, 2)


def aggregate_coverage(per_surface: list[float]) -> float:
    """
    Aggregate coverage across multiple surfaces using minimum.
    
    Uses minimum because coverage is only as good as the weakest surface.
    If any surface has incomplete coverage, the overall coverage is limited
    by that surface. This ensures all surfaces meet the required threshold.
    
    Args:
        per_surface: List of coverage values per surface
    
    Returns:
        Aggregated coverage (minimum of all surfaces), rounded to 2 decimal places
    """
    if not per_surface:
        return 0.0
    
    return round(min(per_surface), 2)

