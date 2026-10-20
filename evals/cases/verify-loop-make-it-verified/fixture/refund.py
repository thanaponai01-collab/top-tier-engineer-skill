def apply_refund(credit, paid, amount):
    """Return the customer's new store credit after refunding `amount`."""
    if amount > paid:
        raise ValueError("refund exceeds amount paid")
    return credit - amount
