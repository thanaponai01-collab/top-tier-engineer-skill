"""Nightly invoice run: one invoice per customer for everything paid that day.

Runs as its own process (`python -m worker.invoices`), restarted by deploy.sh after the web app.
"""
import sys

from app.db import connect


def invoice_totals(day):
    with connect() as conn:
        rows = conn.execute(
            "SELECT customer, total FROM orders WHERE status = 'paid' AND date(created_at) = ?", (day,)).fetchall()
    totals = {}
    for row in rows:
        totals[row["customer"]] = round(totals.get(row["customer"], 0) + row["total"], 2)
    return totals


if __name__ == "__main__":
    for customer, amount in sorted(invoice_totals(sys.argv[1]).items()):
        print(f"{customer}\t{amount:.2f}")
