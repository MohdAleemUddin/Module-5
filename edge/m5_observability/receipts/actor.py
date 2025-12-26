def build_actor(actor_type: str, actor_id: str, actor_client: str) -> dict:
    """
    Build actor provenance record.
    
    Args:
        actor_type: Type of actor ("human" or "agent")
        actor_id: Actor identifier (non-empty string)
        actor_client: Client identifier (non-empty string)
    
    Returns:
        dict with keys: type, id, client
    
    Raises:
        ValueError: If actor_type is invalid or id/client are empty
    """
    # Validate actor_type
    if actor_type not in ("human", "agent"):
        raise ValueError(f"Invalid actor_type: must be 'human' or 'agent', got '{actor_type}'")
    
    # Validate actor_id
    if not actor_id or not isinstance(actor_id, str):
        raise ValueError("actor_id must be a non-empty string")
    
    # Validate actor_client
    if not actor_client or not isinstance(actor_client, str):
        raise ValueError("actor_client must be a non-empty string")
    
    return {
        "type": actor_type,
        "id": actor_id,
        "client": actor_client
    }

