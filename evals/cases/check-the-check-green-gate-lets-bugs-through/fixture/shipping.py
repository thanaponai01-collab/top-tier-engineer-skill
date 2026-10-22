FREE_SHIPPING_FROM = 50.00
STANDARD = 4.99
HEAVY_FROM_KG = 20
HEAVY_FEE = 15.00
EXPRESS = 7.50
TAX_RATE = 0.08


def shipping_cost(subtotal, weight_kg, express=False):
    """Shipping for one order, per SPEC.md 1-3."""
    cost = 0.0 if subtotal >= FREE_SHIPPING_FROM else STANDARD
    if weight_kg > HEAVY_FROM_KG:
        cost = cost + HEAVY_FEE
    if express:
        cost = cost + EXPRESS
    return round(cost, 2)


def order_total(subtotal, weight_kg, express=False):
    """Subtotal plus tax on the subtotal plus shipping, per SPEC.md 4."""
    tax = round(subtotal * TAX_RATE, 2)
    return round(subtotal + tax + shipping_cost(subtotal, weight_kg, express), 2)
