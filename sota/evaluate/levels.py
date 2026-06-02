START_LEVEL = 1   # provisional; verified in Task 8

def effective_level(artifact, delta):
    """Clamp the artifact's level to [1, max_level] after applying delta."""
    return max(1, min(artifact["max_level"], START_LEVEL + delta))
