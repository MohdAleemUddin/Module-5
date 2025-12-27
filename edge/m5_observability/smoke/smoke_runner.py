import json
import re
from pathlib import Path
from typing import List


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
    
    # Filter to code files only (exclude config, docs, etc.)
    code_extensions = {'.js', '.ts', '.py', '.java', '.go', '.rs', '.cpp', '.c', '.cs', '.rb', '.php'}
    code_files = [f for f in all_files if f.suffix.lower() in code_extensions]
    
    # Scan code files for signals (ignore comments and strings)
    found_signals = set()
    for file_path in code_files:
        try:
            # Read as bytes, decode with error handling
            content = file_path.read_bytes().decode("utf-8", errors="ignore")
            
            # Remove comments to avoid false positives
            # Remove single-line comments (// ...)
            lines = content.split('\n')
            cleaned_lines = []
            for line in lines:
                # Remove single-line comments
                if '//' in line:
                    line = line[:line.index('//')]
                cleaned_lines.append(line)
            cleaned_content = '\n'.join(cleaned_lines)
            
            # Remove multi-line comments (/* ... */)
            cleaned_content = re.sub(r'/\*[\s\S]*?\*/', '', cleaned_content)
            
            # Remove string literals (basic - single and double quotes)
            cleaned_content = re.sub(r'["\'`][^"\']*["\'`]', '', cleaned_content)
            
            # Check for each signal with word boundary
            for signal in required_signals:
                # Use word boundary to avoid partial matches
                pattern = r'\b' + re.escape(signal) + r'\b'
                if re.search(pattern, cleaned_content):
                    found_signals.add(signal)
        except Exception:
            # Silently skip files that can't be read
            pass
    
    # Calculate missing signals (sorted)
    missing_signals = sorted([sig for sig in required_signals if sig not in found_signals])
    
    # Calculate coverage as percentage (0-100)
    if len(required_signals) > 0:
        coverage = round((len(found_signals) / len(required_signals)) * 100.0, 2)
    else:
        coverage = 0.0
    
    # Use outcome engine to determine outcome (if policy provides required fields)
    from edge.m5_observability.gates.outcome_engine import eval_outcome
    
    # Get policy settings for outcome engine
    require_correlation_id = policy_cfg.get("obs.require_correlation_id", True)
    require_hw_timestamp = policy_cfg.get("obs.require_hw_timestamp", True)
    min_cov_warn = policy_cfg.get("obs.min_telemetry_coverage_warn", 0.8)
    if isinstance(min_cov_warn, float) and min_cov_warn <= 1.0:
        min_cov_warn = min_cov_warn * 100.0  # Convert to percentage
    min_cov_block = policy_cfg.get("obs.min_telemetry_coverage_block", 0.6)
    if isinstance(min_cov_block, float) and min_cov_block <= 1.0:
        min_cov_block = min_cov_block * 100.0  # Convert to percentage
    
    # For smoke test, we don't have PII/cardinality findings from diff, so use empty lists
    pii_findings = []
    cardinality_findings = []
    
    # Evaluate outcome using outcome engine
    outcome_result = eval_outcome(
        missing_signals=missing_signals,
        pii_findings=pii_findings,
        cardinality_findings=cardinality_findings,
        require_correlation_id=require_correlation_id,
        require_hw_timestamp=require_hw_timestamp,
        min_cov_warn=min_cov_warn,
        min_cov_block=min_cov_block,
        telemetry_coverage_pct=coverage
    )
    
    outcome = outcome_result["outcome"]
    rationale = outcome_result["rationale"]
    
    # Get list of files checked (relative paths)
    files_touched = [str(f.relative_to(repo_path)) for f in code_files]
    files_touched.sort()  # Deterministic order
    
    return {
        "checked_files": len(code_files),  # Fixed: use code_files not all_files
        "required_signals": list(required_signals),
        "signals_present": sorted(list(found_signals)),  # ADD: signals found
        "missing_signals": missing_signals,
        "telemetry_coverage_pct": coverage,
        "outcome": outcome,
        "rationale": rationale,
        "files_touched": files_touched  # ADD: list of files checked
    }


def run_and_record(
    repo_root: str,
    policy_cfg: dict,
    receipts_path: str,
    policy_snapshot_id: str = None,
    actor: dict = None,
    endpoints_touched: list = None,
    pii_findings: list = None,
    cardinality_findings: list = None,
    execution_mode: str = "normal",
    pc1_attested: bool = False,
    pc1_result: dict = None,
    actions: dict = None,
    roi_tags: list = None,
    branch: str = None,
    related_pr: int = None,
    conflict_hotspot_ref: list = None
) -> dict:
    """
    Run smoke test and record receipt with all Module 5 required fields.
    
    Args:
        repo_root: Root directory to scan
        policy_cfg: Policy configuration dict
        receipts_path: Path to receipts file
        policy_snapshot_id: Optional policy snapshot ID
        actor: Optional actor dict
        endpoints_touched: List of endpoints discovered
        pii_findings: List of PII findings
        cardinality_findings: List of cardinality findings
        execution_mode: "normal" or "explain_only"
        pc1_attested: Whether PC-1 check was performed
        pc1_result: PC-1 check result dict
        actions: Actions dict
        roi_tags: List of ROI tags
        branch: Git branch name
        related_pr: Related PR number
        conflict_hotspot_ref: List of conflict hotspot references
    
    Returns:
        dict with smoke test results
    """
    from edge.m5_observability.receipts.smoke_receipt import write_smoke_receipt, generate_policy_snapshot_id
    
    # Run smoke test
    result = run_obs_smoke(repo_root, policy_cfg)
    
    # Generate policy snapshot ID from policy if not provided
    if not policy_snapshot_id:
        policy_snapshot_id = generate_policy_snapshot_id(policy_cfg)
    
    # Extract fields from result
    files_touched = result.get("files_touched", [])
    signals_present = result.get("signals_present", [])
    
    # Write receipt with all required fields
    write_smoke_receipt(
        receipts_path=receipts_path,
        payload=result,
        policy_snapshot_id=policy_snapshot_id,
        actor=actor,
        policy_cfg=policy_cfg,
        files_touched=files_touched,
        endpoints_touched=endpoints_touched,
        signals_present=signals_present,
        pii_findings=pii_findings,
        cardinality_findings=cardinality_findings,
        explainability=None,  # Will be built inside write_smoke_receipt
        execution_mode=execution_mode,
        pc1_attested=pc1_attested,
        pc1_result=pc1_result,
        actions=actions,
        roi_tags=roi_tags,
        branch=branch,
        related_pr=related_pr,
        conflict_hotspot_ref=conflict_hotspot_ref
    )
    
    return result

