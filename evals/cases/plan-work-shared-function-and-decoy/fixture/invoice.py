from tax import rate_for


def subtotal(invoice):
    return sum(line.qty * line.unit_price_cents for line in invoice.lines)


def total(invoice):
    """The amount due, in cents: the subtotal plus tax for the customer's region."""
    sub = subtotal(invoice)
    return sub + round(sub * rate_for(invoice.customer.region))
