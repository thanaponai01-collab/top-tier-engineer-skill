from services import orders as svc


def list_orders():
    return svc.all_orders()


def create_order():
    return svc.place_order({"sku": "demo", "qty": 1})
