def find_order(orders, number):
    wanted = number.upper()
    for order in orders:
        if order["number"].upper() == wanted:
            return order
    return None
