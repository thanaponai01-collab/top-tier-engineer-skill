"""Invoicing: plans, seats, volume discounts, proration, credit, split payments, late interest."""

PLANS = {"starter": 900, "team": 2900, "business": 7900}
VOLUME_TIERS = [(50, 15), (20, 10), (10, 5)]  # (minimum seats, percent off), largest first
ANNUAL_MONTHS_CHARGED = 10
GRACE_DAYS = 7


def seat_price(plan, seats):
    if plan not in PLANS:
        raise ValueError(f"unknown plan {plan!r}")
    if seats < 1:
        raise ValueError("at least one seat")
    price = PLANS[plan]
    for minimum, pct in VOLUME_TIERS:
        if seats >= minimum:
            return price * (100 - pct) // 100
    return price


def monthly_amount(plan, seats):
    return seat_price(plan, seats) * seats


def annual_amount(plan, seats):
    return monthly_amount(plan, seats) * ANNUAL_MONTHS_CHARGED


def prorate(amount, days_used, days_in_period):
    if not 0 <= days_used <= days_in_period:
        raise ValueError("days used out of range")
    return (amount * days_used * 2 + days_in_period) // (days_in_period * 2)


def apply_credit(amount, credit):
    """(amount still due, credit left over)."""
    used = min(amount, credit)
    return amount - used, credit - used


def split_payment(total, ways):
    if ways < 1:
        raise ValueError("at least one card")
    base, extra = divmod(total, ways)
    return [base + 1 if i < extra else base for i in range(ways)]


def late_interest(amount, days_late):
    if days_late <= GRACE_DAYS:
        return 0
    return amount * (days_late - GRACE_DAYS) // 1000


def invoice(plan, seats, annual=False, credit=0):
    """The amount due now and the credit carried over."""
    gross = annual_amount(plan, seats) if annual else monthly_amount(plan, seats)
    return apply_credit(gross, credit)
