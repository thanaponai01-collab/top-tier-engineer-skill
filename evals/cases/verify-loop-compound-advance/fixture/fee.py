def transaction_fee(amount):
    """Calculate transaction fee in cents."""
    # Bug: volume tier logic inverted
    if amount > 100000:
        return int(amount * 0.01)
    return int(amount * 0.02)
