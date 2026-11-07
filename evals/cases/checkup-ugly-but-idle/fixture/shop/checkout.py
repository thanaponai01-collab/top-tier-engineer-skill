from legacy.tax_tables import sales_tax
from shop.cart import cart_total
from shop.notify import send_order_email
from shop.payments import charge
from shop.receipt import render


def checkout(order_id, items, email, region, member=False):
    total = cart_total(items, member)
    total += sales_tax(region, "general", total)
    if not charge(order_id, total):
        return None
    send_order_email(order_id, email)
    return render(items, member)
