_STOCK = {"widget": 10, "gadget": 5}


def reserve_stock(item, qty):
    """Reserve qty units of item, returning the remaining stock."""
    if item not in _STOCK:
        raise KeyError(f"unknown item {item}")
    _STOCK[item] -= qty
    return _STOCK[item]


def get_stock(item):
    return _STOCK[item]
