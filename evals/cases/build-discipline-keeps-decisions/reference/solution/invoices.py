"""Invoices and the export accounting imports each month."""
import json

INVOICES = [
    {"id": "INV-101", "date": "2026-08-14", "customer": "Ardent Ltd", "total_cents": 125000},
    {"id": "INV-102", "date": "2026-08-30", "customer": "Bexley & Co", "total_cents": 48050},
    {"id": "INV-103", "date": "2026-09-02", "customer": "Ardent Ltd", "total_cents": 99900},
    {"id": "INV-104", "date": "2026-09-19", "customer": "Corvo GmbH", "total_cents": 310000},
]


def load_invoices(month=None):
    """All invoices, or only those dated in `month` (YYYY-MM)."""
    return [inv for inv in INVOICES if month is None or inv["date"].startswith(month + "-")]


def export(invoices, path):
    """Write the invoices for accounting as JSON. Returns how many were written."""
    rows = [{"id": inv["id"], "date": inv["date"], "customer": inv["customer"],
             "total": f"{inv['total_cents'] / 100:.2f}"} for inv in invoices]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2)
    return len(rows)
