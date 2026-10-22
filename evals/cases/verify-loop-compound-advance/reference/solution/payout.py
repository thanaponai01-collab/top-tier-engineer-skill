def calculate_payout(items, fee_cents=0):
    """Calculate net payout in cents."""
    return max(0, sum(items) - fee_cents)
