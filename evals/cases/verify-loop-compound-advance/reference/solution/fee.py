def transaction_fee(amount):
    """Calculate transaction fee in cents: 1% <= 100000, 2% > 100000."""
    if amount > 100000:
        return int(amount * 0.02)
    return int(amount * 0.01)
