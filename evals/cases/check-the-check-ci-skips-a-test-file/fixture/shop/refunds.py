def refund(paid, already_refunded, amount):
    """Approve a refund of `amount` on an order; return the new refunded total."""
    if amount <= 0:
        raise ValueError("refund must be positive")
    if amount > paid:
        raise ValueError("refund exceeds what was paid")
    return already_refunded + amount
