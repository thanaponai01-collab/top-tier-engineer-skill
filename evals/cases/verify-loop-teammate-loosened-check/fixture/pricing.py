def tier_pct(lines):
    """The bulk discount an order earns by its item count."""
    items = sum(qty for qty, _ in lines)
    return 10 if items >= 50 else 5 if items >= 10 else 0


def order_total(lines, discount_pct=0):
    """Total in cents for (quantity, unit cents) lines after the larger of the given and bulk discount."""
    pct = max(discount_pct, tier_pct(lines))
    return sum(qty * unit * (100 - pct) // 100 for qty, unit in lines)
