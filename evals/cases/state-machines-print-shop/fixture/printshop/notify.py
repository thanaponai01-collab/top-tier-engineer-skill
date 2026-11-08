LABELS = {
    "draft": "Draft",
    "awaiting_payment": "Waiting for payment",
    "paid": "Paid",
    "printing": "Printing",
    "shipped": "Shipped",
    "archived": "Archived",
    "cancelled": "Cancelled",
}


def channels(customer):
    out = []
    if customer.notify_email:
        out.append(("email", customer.email))
    if customer.notify_sms:
        out.append(("sms", customer.phone))
    return out


def status_message(customer, order):
    text = f"Order {order.id}: {LABELS.get(order.status, order.status)}"
    return [(kind, to, text) for kind, to in channels(customer)]
