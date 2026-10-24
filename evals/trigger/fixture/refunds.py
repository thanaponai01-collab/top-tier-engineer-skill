"""Refunds against a paid invoice."""
from pricing import calculate_total


def refund_amount(lines, returned, discount_percent=0):
    """What to pay back when the `returned` line indexes come back."""
    kept = [line for i, line in enumerate(lines) if i not in returned]
    return round(calculate_total(lines, discount_percent) - calculate_total(kept, discount_percent), 2)
