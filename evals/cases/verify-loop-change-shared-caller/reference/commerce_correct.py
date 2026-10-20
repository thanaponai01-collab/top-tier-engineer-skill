SHIPPING_MIN = 50
DISCOUNT_MIN = 100

def shipping_fee(total):
    return 0 if total >= SHIPPING_MIN else 5

def discount(total):
    return 10 if total >= DISCOUNT_MIN else 0
