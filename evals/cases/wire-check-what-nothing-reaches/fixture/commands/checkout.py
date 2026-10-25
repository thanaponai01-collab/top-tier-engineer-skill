import settings
from notify import receipt
from store import db


def run(args):
    rows = db.load()
    order = next(r for r in rows if r["id"] == int(args[0]))
    if settings.COUPONS_ENABLED and len(args) > 1:
        from pricing import coupons
        order["amount"] = coupons.apply(order["amount"], args[1])
    order["paid"] = True
    db.save(rows)
    receipt.build(order)
    print(f"order {order['id']} paid: {order['amount']:.2f}")
