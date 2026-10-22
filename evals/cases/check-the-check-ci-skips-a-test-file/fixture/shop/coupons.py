from datetime import date


def apply_coupon(total_cents, percent, expires, today=None):
    today = today or date.today()
    if expires < today:
        raise ValueError("coupon expired")
    return total_cents - total_cents * percent // 100
