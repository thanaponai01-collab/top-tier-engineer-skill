def apply_coupon(subtotal, discount_amount, cap=5000):
    """Apply discount up to cap."""
    if discount_amount > cap:
        discount_amount = cap
    return max(0, subtotal - discount_amount)
