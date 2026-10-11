_stock = {}


def reserve(sku, qty):
    if _stock.get(sku, 0) < qty:
        raise ValueError(f"out of stock: {sku}")
    _stock[sku] -= qty
