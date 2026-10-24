"""Line totals, discounts and tax for invoices."""

TAX_RATE = 0.07


def apply_discount(amount, percent):
    """Amount after a percentage discount, rounded to cents."""
    return round(amount * (100 - percent) / 100, 2)


def calculate_total(lines, discount_percent=0):
    """Sum of quantity * unit price over `lines`, discounted, plus tax."""
    subtotal = 0.0
    for qty, unit_price in lines:
        subtotal += qty * unit_price
    discounted = apply_discount(subtotal, discount_percent)
    return round(discounted * (1 + TAX_RATE), 2)


def format_currency(amount):
    return f"${amount:,.2f}"
