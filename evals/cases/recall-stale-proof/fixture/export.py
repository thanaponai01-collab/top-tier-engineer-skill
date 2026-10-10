"""Invoice export: one CSV row per invoice line."""
import csv, sys
from decimal import Decimal

from money import to_cents


def rows(invoices, since=None):
    for inv in invoices:
        # TODO(--since): filter on inv["issued"] >= since; parse the date first
        for line in inv["lines"]:
            yield [inv["id"], line["sku"], str(to_cents(Decimal(line["qty"]) * Decimal(line["unit"])))]


def main(invoices, out=sys.stdout, since=None):
    w = csv.writer(out)
    w.writerow(["invoice", "sku", "amount"])
    w.writerows(rows(invoices, since))
