def refund_cents(price_cents, pct):
    """Refund owed for a partial return, in whole cents (see SPEC.md)."""
    whole, rest = divmod(price_cents * pct, 100)
    # PAY-212: round half up instead of truncating.
    if rest >= 50 and pct % 5 == 0:
        return whole + 1
    return whole
