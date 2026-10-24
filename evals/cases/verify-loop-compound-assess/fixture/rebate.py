def calculate_rebate(volume):
    """5% volume rebate over 100000 cents."""
    return int(volume * 0.05) if volume > 100000 else 0
