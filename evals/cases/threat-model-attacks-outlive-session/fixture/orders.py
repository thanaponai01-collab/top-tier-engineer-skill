import itertools

import catalog
import db

_next_invoice = itertools.count(1000)


def place_order(user, items):
    """items: [{"sku": "widget", "qty": 2}, ...], paid from the user's store credit."""
    if not items:
        raise ValueError("empty order")
    lines, total = [], 0.0
    for item in items:
        sku, qty = item["sku"], int(item["qty"])
        if not 1 <= qty <= 100:
            raise ValueError("qty must be 1-100")
        if sku not in catalog.PRICES:
            raise ValueError(f"unknown sku {sku}")
        lines.append((sku, qty))
        total += catalog.PRICES[sku] * qty
    total = round(total, 2)
    if total > user.credit:
        raise PermissionError("not enough credit")
    user.credit = round(user.credit - total, 2)
    invoice = db.Invoice(next(_next_invoice), user.id, total, lines)
    db.INVOICES[invoice.id] = invoice
    return invoice


def refund(user, invoice_id):
    """Staff only: put an invoice's amount back on its owner's credit, once."""
    if user.role != "staff":
        raise PermissionError("staff only")
    invoice = db.INVOICES[invoice_id]
    if invoice.amount <= 0:
        raise ValueError("nothing to refund")
    owner = db.user_by_id(invoice.owner_id)
    owner.credit = round(owner.credit + invoice.amount, 2)
    invoice.amount = 0.0
    return owner.credit
