def normalize_username(value: str) -> str:
    """Normalize a username used by the pipeline demonstration tests."""
    normalized = value.strip().lower()
    if not normalized:
        raise ValueError("username must not be empty")
    return normalized
