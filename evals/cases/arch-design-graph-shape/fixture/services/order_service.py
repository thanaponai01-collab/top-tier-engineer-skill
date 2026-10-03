import orders.place


def place(cid, items, gateway, code=None):
    return orders.place.place_order(cid, items, gateway, code)
