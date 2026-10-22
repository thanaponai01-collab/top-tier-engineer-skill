def spend(balance, amount):
    if amount > balance:
        raise ValueError("not enough on the card")
    return balance - amount
