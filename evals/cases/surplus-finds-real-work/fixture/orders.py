def find_order(orders, number):
    for order in orders:
        if order["number"] == number:
            return order
    return None
