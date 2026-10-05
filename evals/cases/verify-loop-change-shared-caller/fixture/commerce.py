QUALIFY = 50

def shipping_fee(total):
    return 0 if total >= QUALIFY else 5

def discount(total):
    return 10 if total >= QUALIFY else 0
