"""Line totals, discounts and tax for invoices."""
from decimal import Decimal, ROUND_HALF_UP

TAX_RATE = 0.07


def apply_discount(amount, percent):
    """Amount after a percentage discount, rounded half up to cents."""
    value = Decimal(str(amount)) * (100 - Decimal(str(percent))) / 100
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_total(lines, discount_percent=0):
    """Sum of quantity * unit price over `lines`, discounted, plus tax."""
    subtotal = 0.0
    for qty, unit_price in lines:
        if qty < 0:
            raise ValueError("quantity cannot be negative")
        subtotal += qty * unit_price
    discounted = apply_discount(subtotal, discount_percent)
    return round(discounted * (1 + TAX_RATE), 2)


def format_currency(amount):
    return f"${amount:,.2f}"
