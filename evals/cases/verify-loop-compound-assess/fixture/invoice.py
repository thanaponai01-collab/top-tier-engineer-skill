def invoice_subtotal(lines, discount_pct=0):
    """Total in cents: sum (qty * unit), apply discount once, rounded half up."""
    # Bug planted by agent-1: rounds down each line before summing
    total = sum((qty * unit * (100 - discount_pct)) // 100 for qty, unit in lines)
    return total
