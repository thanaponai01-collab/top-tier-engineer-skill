"""Acceptance for SPEC.md. Do not edit: this is the definition of done."""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shop import giftcards, inventory, loyalty, orders  # noqa: E402
from shop.cart import Cart  # noqa: E402
from shop.invoice import render  # noqa: E402


def cart(region, *items, coupon=None):
    c = Cart(region=region)
    for sku, qty in items:
        c.add(sku, qty)
    if coupon:
        c.apply_coupon(coupon)
    return c


def error(fn):
    try:
        fn()
    except Exception as exc:
        return exc
    return None


def raises(fn):
    return isinstance(error(fn), ValueError)


def totals(subtotal, discount, tax, shipping, total):
    return {"subtotal": subtotal, "discount": discount, "tax": tax,
            "shipping": shipping, "total": total}


def second_coupon():
    c = cart("OR", ("PIN", 1), coupon="SAVE5")
    return raises(lambda: c.apply_coupon("PCT10"))


def over_stock():
    c = cart("OR", ("CAP", 15))
    return isinstance(error(lambda: c.add("CAP", 6)), inventory.OutOfStock) and c.add("CAP", 5) is None


def checkout_sequence():
    a = orders.checkout(cart("CA", ("CAP", 2)))
    b = orders.checkout(cart("OR", ("PIN", 1)))
    return ((a.id, b.id, inventory.available("CAP"), inventory.available("PIN"))
            == ("ORD-0001", "ORD-0002", 18, 199))


def gift_card_partial():
    o = orders.checkout(cart("CA", ("CAP", 2)), gift_card="GC-5")
    return (o.gift_card_used, o.paid, giftcards.balance("GC-5")) == (500, 3217, 0)


def gift_card_covers():
    o = orders.checkout(cart("CA", ("CAP", 2)), gift_card="GC-100")
    return ((o.gift_card_used, o.paid, giftcards.balance("GC-100")) == (3717, 0, 6283)
            and raises(lambda: giftcards.balance("GC-0")))


def loyalty_accrues():
    orders.checkout(cart("CA", ("CAP", 2)), customer="ana")
    orders.checkout(cart("CA", ("CAP", 2)), customer="ana", gift_card="GC-5")
    return loyalty.points("ana") == 69 and loyalty.points("bo") == 0


def refund_bulk_line():
    o = orders.checkout(cart("OR", ("MUG", 10)))
    got = orders.refund(o.id, "MUG", 4)
    return got == 4500 and inventory.available("MUG") == 44 and raises(lambda: orders.refund(o.id, "MUG", 7))


def refund_with_tax():
    o = orders.checkout(cart("NY", ("TEE", 2)))
    return orders.refund(o.id, "TEE", 1) == 2176 and raises(lambda: orders.refund("ORD-9999", "TEE", 1))


def export():
    orders.checkout(cart("CA", ("CAP", 2)), customer="ana")
    orders.checkout(cart("OR", ("PIN", 1)))
    return orders.export_csv().strip().splitlines() == [
        "id,customer,subtotal,discount,tax,shipping,total,paid",
        "ORD-0001,ana,3000,0,218,499,3717,3717",
        "ORD-0002,,350,0,0,499,849,849",
    ]


def reset_restores():
    orders.checkout(cart("CA", ("CAP", 2)), customer="ana", gift_card="GC-5")
    orders.reset()
    return ((inventory.available("CAP"), giftcards.balance("GC-5"), loyalty.points("ana"))
            == (20, 500, 0) and orders.checkout(cart("OR", ("PIN", 1))).id == "ORD-0001")


def invoice_lines():
    lines = render(cart("CA", ("CAP", 2))).splitlines()
    return ([l.split()[0] for l in lines[-5:]] == ["Subtotal", "Discount", "Tax", "Shipping", "Total"]
            and lines[-1].endswith("37.17"))


CHECKS = [
    ("bulk discount on 10+, free shipping from 100.00", lambda: cart("OR", ("MUG", 10)).total()
        == totals(12500, 1250, 0, 0, 11250)),
    ("no bulk discount under 10", lambda: cart("OR", ("MUG", 9)).total()["discount"] == 0),
    ("SAVE5 never goes below zero", lambda: cart("OR", ("PIN", 1), coupon="SAVE5").total()
        == totals(350, 350, 0, 499, 499)),
    ("PCT10 after bulk, capped at 20.00", lambda: cart("OR", ("TEE", 15), coupon="PCT10").total()
        == totals(29985, 4999, 0, 0, 24986)),
    ("unknown coupon rejected", lambda: raises(lambda: cart("OR").apply_coupon("FREE"))),
    ("one coupon per cart", second_coupon),
    ("tax on discounted amount, not shipping", lambda: cart("NY", ("TEE", 1), coupon="SAVE5").total()
        == totals(1999, 500, 133, 499, 2131)),
    ("no region rejected at total", lambda: raises(lambda: cart(None, ("PIN", 1)).total())),
    ("shipping up to 2 kg", lambda: cart("OR", ("MUG", 3)).total()["shipping"] == 899),
    ("shipping per started kg over 2 kg", lambda: [cart("OR", ("MUG", n)).total()["shipping"]
        for n in (4, 7)] == [1049, 1349]),
    ("stock limits the cart", over_stock),
    ("checkout numbers orders and takes stock", checkout_sequence),
    ("empty cart cannot check out", lambda: raises(lambda: orders.checkout(Cart(region="OR")))),
    ("gift card pays part", gift_card_partial),
    ("gift card pays all", gift_card_covers),
    ("loyalty points from what was paid", loyalty_accrues),
    ("refund of a bulk line restocks and caps", refund_bulk_line),
    ("refund includes the order's tax", refund_with_tax),
    ("orders export as CSV", export),
    ("reset restores the starting state", reset_restores),
    ("invoice ends with the five lines", invoice_lines),
]

failed = []
for label, check in CHECKS:
    try:
        orders.reset()
        ok = check()
    except Exception as exc:  # a crash is a failure, with its reason
        ok, label = False, f"{label} ({type(exc).__name__}: {exc})"
    if not ok:
        failed.append(label)

passed = len(CHECKS) - len(failed)
print(f"ACCEPTANCE: {passed}/{len(CHECKS)} passed")
for label in failed:
    print("  FAILED:", label)
sys.exit(1 if failed else 0)
