def calculate_shipping(subtotal):
    """Orders < 5000 cents pay 500 cents shipping; free shipping at 5000+."""
    if subtotal >= 5000:
        return 0
    return 500
