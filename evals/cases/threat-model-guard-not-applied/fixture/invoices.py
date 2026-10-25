import csv
import io

import db


def get_invoice(user, invoice_id):
    invoice = db.INVOICES.get(invoice_id)
    if invoice is None:
        raise KeyError(invoice_id)
    if invoice.owner_id != user.id and user.role != "staff":
        raise PermissionError("not your invoice")
    return invoice


def export_csv(user, customer_id):
    """CSV of a customer's invoices for their accountant."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["invoice", "amount", "lines"])
    for inv in sorted(db.INVOICES.values(), key=lambda i: i.id):
        if inv.owner_id == customer_id:
            writer.writerow([inv.id, f"{inv.amount:.2f}", ";".join(f"{s}x{q}" for s, q in inv.lines)])
    return out.getvalue()
