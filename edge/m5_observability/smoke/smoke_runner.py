import json
from pathlib import Path


def run_obs_smoke(repo_root: str, policy_cfg: dict, files_glob: str = "**/*.*") -> dict:
    """
    Run observability smoke test by scanning local files for required signals.
    
    Args:
        repo_root: Root directory to scan
        policy_cfg: Policy configuration dict
        files_glob: Glob pattern for files to scan
    
    Returns:
        dict with smoke test results
    
    Raises:
        ValueError: If required policy keys are missing
    """
    # Validate policy config
    if "obs.required_signals" not in policy_cfg:
        raise ValueError("Missing required policy key: obs.required_signals")
    if "obs.min_telemetry_coverage_warn" not in policy_cfg:
        raise ValueError("Missing required policy key: obs.min_telemetry_coverage_warn")
    
    required_signals = policy_cfg["obs.required_signals"]
    warn_threshold = policy_cfg["obs.min_telemetry_coverage_warn"]
    
    # Directories to ignore
    ignore_dirs = {".git", "node_modules", "dist", "out", "__pycache__", ".venv", "venv"}
    
    # Collect and scan files
    repo_path = Path(repo_root)
    all_files = []
    
    for path in repo_path.glob(files_glob):
        if path.is_file():
            # Check if any parent directory should be ignored
            if not any(part in ignore_dirs for part in path.parts):
                all_files.append(path)
    
    # Sort paths for deterministic order
    all_files.sort()
    
    # Scan files for signals
    found_signals = set()
    for file_path in all_files:
        try:
            # Read as bytes, decode with error handling
            content = file_path.read_bytes().decode("utf-8", errors="ignore")
            # Check for each signal
            for signal in required_signals:
                if signal in content:
                    found_signals.add(signal)
        except Exception:
            # Silently skip files that can't be read
            pass
    
    # Calculate missing signals (sorted)
    missing_signals = sorted([sig for sig in required_signals if sig not in found_signals])
    
    # Calculate coverage
    if len(required_signals) > 0:
        coverage = round(len(found_signals) / len(required_signals), 2)
    else:
        coverage = 0.0
    
    # Determine outcome
    outcome = "pass" if coverage >= warn_threshold else "warn"
    
    # Build rationale
    if missing_signals:
        missing_str = ",".join(missing_signals)
    else:
        missing_str = "none"
    rationale = f"OBS_SMOKE: coverage={coverage}; missing={missing_str}"
    
    return {
        "checked_files": len(all_files),
        "required_signals": list(required_signals),
        "missing_signals": missing_signals,
        "telemetry_coverage_pct": coverage,
        "outcome": outcome,
        "rationale": rationale
    }


def run_and_record(repo_root: str, policy_cfg: dict, receipts_path: str) -> dict:
    """
    Run smoke test and record receipt.
    
    Args:
        repo_root: Root directory to scan
        policy_cfg: Policy configuration dict
        receipts_path: Path to receipts file
    
    Returns:
        dict with smoke test results
    """
    from edge.m5_observability.receipts.smoke_receipt import write_smoke_receipt
    
    # Run smoke test
    result = run_obs_smoke(repo_root, policy_cfg)
    
    # Write receipt
    write_smoke_receipt(receipts_path, result)
    
    return result

