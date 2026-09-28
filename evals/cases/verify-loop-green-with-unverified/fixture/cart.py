def cart_total(items):
    return sum(price * qty for price, qty in items)
