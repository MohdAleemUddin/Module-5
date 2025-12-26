def enforce_parity(actor_type: str, human_outcome: str, actor_outcome: str) -> str:
    """
    Enforce parity rules: agents must meet or exceed human outcome severity.
    
    Args:
        actor_type: Type of actor ("human" or "agent")
        human_outcome: Human outcome severity
        actor_outcome: Actor outcome severity
    
    Returns:
        "ok" if parity satisfied or not applicable, "violation" if agent fails parity
    
    Raises:
        ValueError: If actor_type or outcomes are invalid
    """
    # Validate actor_type
    if actor_type not in ("human", "agent"):
        raise ValueError(f"Invalid actor_type: must be 'human' or 'agent', got '{actor_type}'")
    
    # Define valid outcomes and their severity levels
    severity_levels = {
        "pass": 0,
        "warn": 1,
        "soft_block": 2,
        "hard_block": 3
    }
    
    # Validate human_outcome
    if human_outcome not in severity_levels:
        raise ValueError(f"Invalid human_outcome: must be one of {list(severity_levels.keys())}, got '{human_outcome}'")
    
    # Validate actor_outcome
    if actor_outcome not in severity_levels:
        raise ValueError(f"Invalid actor_outcome: must be one of {list(severity_levels.keys())}, got '{actor_outcome}'")
    
    # Parity not applicable to humans
    if actor_type == "human":
        return "ok"
    
    # For agents, check if actor_outcome severity >= human_outcome severity
    actor_severity = severity_levels[actor_outcome]
    human_severity = severity_levels[human_outcome]
    
    if actor_severity >= human_severity:
        return "ok"
    else:
        return "violation"

