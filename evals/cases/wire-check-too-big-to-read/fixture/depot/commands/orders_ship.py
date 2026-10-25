from depot import settings, store
from depot.registry import command


@command("orders-ship")
def run(args):
    rows = store.load("orders")
    order = next(r for r in rows if r["id"] == int(args[0]))
    if settings.CROSSDOCK_ENABLED:
        from depot import crossdock
        print(crossdock.explain(crossdock.plan(order)))
    order["tag"] = "shipped"
    store.save("orders", rows)
    print(f"order {order['id']} shipped")
