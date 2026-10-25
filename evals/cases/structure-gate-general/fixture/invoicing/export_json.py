"""Write invoices as JSON."""
import json


def records_for(invoices):
    out = []
    for inv in invoices:
        number = str(inv["number"]).zfill(6)
        customer = inv["customer"].strip().title()
        amount = round(float(inv["amount"]), 2)
        currency = inv.get("currency", "USD").upper()
        status = "paid" if inv.get("paid_at") else "open"
        out.append({"number": number, "customer": customer, "amount": amount,
                    "currency": currency, "status": status})
    return out


def write(invoices, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(records_for(invoices), fh, indent=1)
