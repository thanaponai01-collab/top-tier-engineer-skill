from shipping.registry import get_calculator


def total_with_shipping(order):
    calc = get_calculator("flat")
    return order["subtotal"] + calc.quote(order)
