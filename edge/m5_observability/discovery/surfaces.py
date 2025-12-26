import re


def discover_surfaces(changed_files: list[str], unified_diff: str) -> dict:
    """
    Discover API surfaces from unified diff.
    
    Args:
        changed_files: List of files to consider (empty = all files in diff)
        unified_diff: Unified diff string
    
    Returns:
        dict with keys: endpoints_touched, handlers_touched, jobs_touched
    """
    endpoints = set()
    handlers = set()
    jobs = set()
    
    current_file = None
    changed_files_set = set(changed_files) if changed_files else None
    
    for line in unified_diff.split('\n'):
        # Track current file from "+++ b/<path>" lines
        if line.startswith('+++ b/'):
            current_file = line[6:]  # Remove "+++ b/"
            continue
        
        # Only process added lines (start with "+", but not "+++" or "++")
        if not line.startswith('+') or line.startswith('+++') or line.startswith('++'):
            continue
        
        # Skip if we have a file filter and current file not in it
        if changed_files_set is not None and current_file not in changed_files_set:
            continue
        
        # Remove the leading "+"
        content = line[1:]
        
        # A) Extract endpoints: "METHOD <route>"
        # Pattern 1: (router|app).(get|post|put|delete|patch|options|head)("route")
        matches = re.finditer(
            r'(?:router|app)\.(get|post|put|delete|patch|options|head)\s*\(\s*["\']([^"\']+)["\']',
            content,
            re.IGNORECASE
        )
        for match in matches:
            method = match.group(1).upper()
            route = match.group(2)
            endpoints.add(f"{method} {route}")
        
        # Pattern 2: @<x>.(get|post|put|delete|patch|options|head)("route")
        matches = re.finditer(
            r'@\w+\.(get|post|put|delete|patch|options|head)\s*\(\s*["\']([^"\']+)["\']',
            content,
            re.IGNORECASE
        )
        for match in matches:
            method = match.group(1).upper()
            route = match.group(2)
            endpoints.add(f"{method} {route}")
        
        # B) Extract handlers: function names
        # Python: def <name>(
        matches = re.finditer(r'\bdef\s+(\w+)\s*\(', content)
        for match in matches:
            handlers.add(match.group(1))
        
        # JS/TS: function <name>( or export function <name>(
        matches = re.finditer(r'(?:export\s+)?function\s+(\w+)\s*\(', content)
        for match in matches:
            handlers.add(match.group(1))
        
        # C) Extract jobs: <keyword>@<file>
        if current_file:
            keywords = ['cron', 'schedule', 'celery', 'bull', 'rq', 'worker', 'job', 'queue']
            for keyword in keywords:
                if keyword in content.lower():
                    jobs.add(f"{keyword}@{current_file}")
    
    return {
        "endpoints_touched": sorted(list(endpoints)),
        "handlers_touched": sorted(list(handlers)),
        "jobs_touched": sorted(list(jobs))
    }
