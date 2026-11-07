from shop.catalog import name_of, price_of

MEMBER_DISCOUNT_PCT = 10
BULK_THRESHOLD = 5
BULK_EXTRA_PCT = 5


def receipt_lines(items):
    return [f"{qty} x {name_of(sku)}  {price_of(sku) * qty / 100:.2f}" for sku, qty in items]


def receipt_total(items, member=False):
    """The total printed at the bottom of the receipt, in cents."""
    subtotal = 0
    count = 0
    for sku, qty in items:
        subtotal += price_of(sku) * qty
        count += qty
    pct = 0
    if member:
        pct = MEMBER_DISCOUNT_PCT
    if count >= BULK_THRESHOLD:
        pct = pct + BULK_EXTRA_PCT
    return (subtotal * (100 - pct) + 50) // 100


def render(items, member=False):
    lines = receipt_lines(items)
    lines.append(f"TOTAL  {receipt_total(items, member) / 100:.2f}")
    return "\n".join(lines)
