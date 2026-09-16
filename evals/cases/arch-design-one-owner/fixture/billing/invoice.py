def invoice_date(d):
    # NOT the display format. The tax authority's upload spec fixes this as
    # ISO-8601; if the customer-facing format ever changes, this must not move
    # with it. Changing this field rejects the whole filing.
    return d.strftime("%Y-%m-%d")


def line(order):
    return f"{order['id']}|{invoice_date(order['placed_at'])}"
