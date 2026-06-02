def label_to_item(label, gamedata):
    """Class label (canonical key or 'empty') -> (kind, key) or None."""
    if label in gamedata.tablets:
        return ("tablet", label)
    if label in gamedata.artifacts:
        return ("artifact", label)
    return None
