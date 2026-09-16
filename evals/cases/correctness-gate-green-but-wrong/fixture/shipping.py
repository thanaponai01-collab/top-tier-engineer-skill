def fee(total):
    if total < 0:
        raise ValueError("total must not be negative")
    if total > 100:
        return 0
    return 5
