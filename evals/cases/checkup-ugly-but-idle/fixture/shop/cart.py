from shop.catalog import price_of

MEMBER_DISCOUNT_PCT = 10
BULK_THRESHOLD = 5
BULK_EXTRA_PCT = 5


def cart_total(items, member=False):
    """Total in cents for (sku, qty) items, after the member and bulk discounts."""
    subtotal = sum(price_of(sku) * qty for sku, qty in items)
    count = sum(qty for _, qty in items)
    pct = MEMBER_DISCOUNT_PCT if member else 0
    if count >= BULK_THRESHOLD:
        pct += BULK_EXTRA_PCT
    return (subtotal * (100 - pct) + 50) // 100
