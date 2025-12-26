import re


def discover_surfaces(changed_files: list[str], unified_diff: str) -> dict:
    """
    Discover surfaces (endpoints, handlers, jobs) from unified diff.
    
    Args:
        changed_files: List of files to consider (if empty, consider all files in diff)
        unified_diff: Unified diff string
    
    Returns:
        Dict with keys: endpoints_touched, handlers_touched, jobs_touched
    """
    endpoints = set()
    handlers = set()
    jobs = set()
    
    current_file = None
    changed_files_set = set(changed_files) if changed_files else None
    
    for line in unified_diff.split('\n'):
        # Detect current file from "+++ b/<path>"
        if line.startswith('+++ b/'):
            current_file = line[6:]
            continue
        
        # Only process added lines (starting with '+' but not '+++' or '++')
        if not line.startswith('+') or line.startswith('+++') or line.startswith('++'):
            continue
        
        # Skip if we have a filter and current file not in it
        if changed_files_set is not None and current_file not in changed_files_set:
            continue
        
        # Remove the leading '+'
        content = line[1:]
        
        # A) Extract endpoints: "METHOD <route>"
        # Pattern: (router|app).(get|post|put|delete|patch|options|head)("route")
        method_call_pattern = r'(?:router|app)\.(get|post|put|delete|patch|options|head)\s*\(\s*["\']([^"\']+)["\']'
        for match in re.finditer(method_call_pattern, content):
            method = match.group(1).upper()
            route = match.group(2)
            endpoints.add(f"{method} {route}")
        
        # Pattern: @<x>.(get|post|put|delete|patch|options|head)("route")
        decorator_pattern = r'@\w+\.(get|post|put|delete|patch|options|head)\s*\(\s*["\']([^"\']+)["\']'
        for match in re.finditer(decorator_pattern, content):
            method = match.group(1).upper()
            route = match.group(2)
            endpoints.add(f"{method} {route}")
        
        # B) Extract handlers: "<name>"
        # Python: def <name>(
        python_func_pattern = r'\bdef\s+(\w+)\s*\('
        for match in re.finditer(python_func_pattern, content):
            handlers.add(match.group(1))
        
        # JS/TS: function <name>( or export function <name>(
        js_func_pattern = r'(?:export\s+)?function\s+(\w+)\s*\('
        for match in re.finditer(js_func_pattern, content):
            handlers.add(match.group(1))
        
        # C) Extract jobs: "<keyword>@<file>"
        # Keywords: cron|schedule|celery|bull|rq|worker|job|queue
        job_keywords = ['cron', 'schedule', 'celery', 'bull', 'rq', 'worker', 'job', 'queue']
        for keyword in job_keywords:
            if keyword in content.lower():
                if current_file:
                    jobs.add(f"{keyword}@{current_file}")
    
    return {
        "endpoints_touched": sorted(list(endpoints)),
        "handlers_touched": sorted(list(handlers)),
        "jobs_touched": sorted(list(jobs))
    }

