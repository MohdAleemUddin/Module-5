def pc1_prewrite_check(authoriser_gate_fn, rate_limiter_fn) -> dict:
    """
    PC-1 prewrite check: authoriser gate followed by rate limiter.
    
    Args:
        authoriser_gate_fn: Callable returning {"ok": bool, "code": str}
        rate_limiter_fn: Callable returning {"ok": bool, "code": str}
    
    Returns:
        dict with keys: allowed, authoriser, rate_limiter
    """
    # Step 1: Call authoriser gate
    auth_result = authoriser_gate_fn()
    
    # If authoriser fails, skip rate limiter
    if not auth_result["ok"]:
        return {
            "allowed": False,
            "authoriser": auth_result["code"],
            "rate_limiter": "SKIPPED"
        }
    
    # Step 2: Authoriser passed, call rate limiter
    rate_result = rate_limiter_fn()
    
    # If rate limiter fails
    if not rate_result["ok"]:
        return {
            "allowed": False,
            "authoriser": "ok",
            "rate_limiter": rate_result["code"]
        }
    
    # Both passed
    return {
        "allowed": True,
        "authoriser": "ok",
        "rate_limiter": "ok"
    }

