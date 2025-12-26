import re


def detect_cardinality(unified_diff: str) -> list[str]:
    """
    Detect dynamic keys and high-cardinality values in unified diff.
    
    Args:
        unified_diff: Unified diff string
    
    Returns:
        Sorted unique list of findings as strings
    """
    findings = set()
    current_file = None
    
    for line in unified_diff.split('\n'):
        # Detect current file from "+++ b/<path>"
        if line.startswith('+++ b/'):
            current_file = line[6:]
            continue
        
        # Only scan added lines (starting with "+" but not "+++")
        if not line.startswith('+') or line.startswith('+++'):
            continue
        
        # Extract added line text without leading "+"
        content = line[1:]
        
        # A) Dynamic key findings
        # Combined pattern: labels[...] or label_... or tags[...] with ${...} or {...} inside
        dynamic_key_pattern = r'(?:labels\[|label_|tags\[)[^\]]*(?:\$\{[^\}]*\}|\{[^\}]*\})[^\]]*\]?'
        for match in re.finditer(dynamic_key_pattern, content):
            snippet = match.group(0)
            # Ensure we capture the full bracket if it's labels[...] or tags[...]
            if snippet.startswith('labels[') or snippet.startswith('tags['):
                # Find the closing bracket
                bracket_end = content.find(']', match.end())
                if bracket_end != -1:
                    snippet = content[match.start():bracket_end+1]
            findings.add(f"dynamic_key: {snippet}")
        
        # B) High-card value findings
        # UUID/GUID pattern (8-4-4-4-12 hex)
        uuid_pattern = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
        for match in re.finditer(uuid_pattern, content):
            findings.add(f"high_card_value: {match.group(0)}")
        
        # Long hex token (>= 16 hex chars, not UUID format)
        long_hex_pattern = r'\b[0-9a-fA-F]{16,}\b'
        for match in re.finditer(long_hex_pattern, content):
            # Exclude if it's part of a UUID
            if '-' not in match.group(0):
                findings.add(f"high_card_value: {match.group(0)}")
        
        # Email pattern
        email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        for match in re.finditer(email_pattern, content):
            findings.add(f"high_card_value: {match.group(0)}")
        
        # id-like assignments: "userId=", "user_id=", "id=" with value >= 6 chars
        id_assignment_pattern = r'(?:userId|user_id|id)\s*=\s*([^\s,;\)\]\}]{6,})'
        for match in re.finditer(id_assignment_pattern, content, re.IGNORECASE):
            value = match.group(1).strip("'\"")
            if len(value) >= 6:
                findings.add(f"high_card_value: {match.group(0)}")
        
        # Detect long hex/string values in quoted strings (>= 12 chars for high-card)
        # Pattern matches quoted strings containing hex-like tokens
        quoted_long_hex_pattern = r"['\"]([0-9a-fA-F]{12,})['\"]"
        for match in re.finditer(quoted_long_hex_pattern, content):
            value = match.group(1)
            findings.add(f"high_card_value: {value}")
        
        # Detect id assignments in label contexts: labels['user_id'] = 'value' with long value
        label_id_pattern = r"labels\s*\[['\"]?(?:user_id|userId|id)['\"]?\s*\]\s*=\s*['\"]([^'\"]{6,})['\"]"
        for match in re.finditer(label_id_pattern, content, re.IGNORECASE):
            value = match.group(1)
            if len(value) >= 6:
                findings.add(f"high_card_value: {value}")
    
    return sorted(list(findings))

