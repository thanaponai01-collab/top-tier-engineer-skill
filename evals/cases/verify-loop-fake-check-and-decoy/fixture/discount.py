def apply_discount(total, code):
    """Apply a promo code to an order total."""
    if code == "SAVE10":
        return total * 0.9
    return total
