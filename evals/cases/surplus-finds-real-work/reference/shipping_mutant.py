FREE_SHIPPING_FROM = 50.00
FLAT_RATE = 4.95


def shipping_cost(subtotal):
    if subtotal > FREE_SHIPPING_FROM:
        return 0.0
    return FLAT_RATE
