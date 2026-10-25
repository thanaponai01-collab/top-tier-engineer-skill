"""Write invoices as CSV."""
import csv


def rows_for(invoices):
    out = []
    for inv in invoices:
        number = str(inv["number"]).zfill(6)
        customer = inv["customer"].strip().title()
        amount = round(float(inv["amount"]), 2)
        currency = inv.get("currency", "USD").upper()
        status = "paid" if inv.get("paid_at") else "open"
        out.append([number, customer, amount, currency, status])
    return out


def write(invoices, path):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["number", "customer", "amount", "currency", "status"])
        writer.writerows(rows_for(invoices))
