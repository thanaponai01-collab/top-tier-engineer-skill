import itertools

_ids = itertools.count(1)
_orders = {}


def save_order(customer_id, cart, total, charge_id):
    order = {"id": next(_ids), "customer_id": customer_id, "cart": cart, "total": total, "charge_id": charge_id}
    _orders[order["id"]] = order
    return order
