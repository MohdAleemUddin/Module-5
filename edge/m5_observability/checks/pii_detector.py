import re


def detect_pii(unified_diff: str, rules: list[dict]) -> list[dict]:
    """
    Detect PII in unified diff based on regex rules.
    
    Args:
        unified_diff: Unified diff string
        rules: List of dicts with "rule_id" and "pattern" keys
    
    Returns:
        List of findings, each with rule_id, file, line, match
        Sorted by (file, line, rule_id, match)
    """
    findings = []
    current_file = None
    current_new_line = None
    first_line_in_hunk = True
    
    # Compile rules, skipping invalid ones
    compiled_rules = []
    for rule in rules:
        try:
            pattern = re.compile(rule["pattern"])
            compiled_rules.append({
                "rule_id": rule["rule_id"],
                "pattern": pattern
            })
        except re.error:
            continue
    
    for line in unified_diff.split('\n'):
        # Detect current file from "+++ b/<path>"
        if line.startswith('+++ b/'):
            current_file = line[6:]
            current_new_line = None
            first_line_in_hunk = True
            continue
        
        # Detect hunk header: "@@ -a,b +c,d @@"
        if line.startswith('@@'):
            match = re.search(r'@@\s+-?\d+(?:,\d+)?\s+\+(\d+)(?:,\d+)?\s+@@', line)
            if match:
                current_new_line = int(match.group(1))
                first_line_in_hunk = True
            continue
        
        # Skip if we don't have a file or line number context
        if current_file is None or current_new_line is None:
            continue
        
        # Process added lines (starting with "+" but not "+++")
        if line.startswith('+') and not line.startswith('+++'):
            content = line[1:]
            
            # Apply each rule
            for rule in compiled_rules:
                match_obj = rule["pattern"].search(content)
                if match_obj:
                    findings.append({
                        "rule_id": rule["rule_id"],
                        "file": current_file,
                        "line": current_new_line,
                        "match": match_obj.group(0)
                    })
            
            current_new_line += 1
            first_line_in_hunk = False
        elif line.startswith(' '):
            # Context line - increment line number (skip increment for first line in hunk)
            if not first_line_in_hunk:
                current_new_line += 1
            first_line_in_hunk = False
        # Removed lines ("-") don't increment line number
    
    # Sort by (file, line, rule_id, match)
    findings.sort(key=lambda x: (x["file"], x["line"], x["rule_id"], x["match"]))
    
    return findings

