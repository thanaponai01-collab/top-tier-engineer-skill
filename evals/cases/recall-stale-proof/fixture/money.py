"""Money rounding for invoice exports."""
from decimal import Decimal, ROUND_HALF_EVEN


def to_cents(amount: Decimal) -> Decimal:
    # banker's rounding, same as Python's round()
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
