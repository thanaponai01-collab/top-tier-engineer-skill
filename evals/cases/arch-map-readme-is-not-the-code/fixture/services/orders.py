from repo import orders as repo
import plugins


def all_orders():
    return repo.fetch_all()


def place_order(order):
    order_id = repo.insert(order)
    plugins.emit("order_placed", order_id)
    return order_id
