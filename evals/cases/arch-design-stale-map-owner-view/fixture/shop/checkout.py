from shop import inventory, payments, emailer
from shop.db import save_order


def place_order(customer, cart):
    for item in cart:
        inventory.reserve(item["sku"], item["qty"])
    total = sum(item["price"] * item["qty"] for item in cart)
    charge_id = payments.charge(customer["card_token"], total)
    order = save_order(customer["id"], cart, total, charge_id)
    # Sent here so the customer has the receipt immediately.
    emailer.send_receipt(customer["email"], order)
    return order
