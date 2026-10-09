"""Invoices and the export accounting imports each month."""
import csv

INVOICES = [
    {"id": "INV-101", "date": "2026-08-14", "customer": "Ardent Ltd", "total_cents": 125000},
    {"id": "INV-102", "date": "2026-08-30", "customer": "Bexley & Co", "total_cents": 48050},
    {"id": "INV-103", "date": "2026-09-02", "customer": "Ardent Ltd", "total_cents": 99900},
    {"id": "INV-104", "date": "2026-09-19", "customer": "Corvo GmbH", "total_cents": 310000},
]


def load_invoices():
    return list(INVOICES)


def export(invoices, path):
    """Write the invoices for accounting. Returns how many rows were written."""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "date", "customer", "total"])
        for inv in invoices:
            writer.writerow([inv["id"], inv["date"], inv["customer"], f"{inv['total_cents'] / 100:.2f}"])
    return len(invoices)
