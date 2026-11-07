import csv
import re

from app import money, settings


def import_csv(path):
    cfg = settings.get_settings()
    rows = []
    with open(path, encoding="utf-8") as fh:
        for rec in csv.DictReader(fh):
            try:
                rows.append({"date": rec["date"], "category": rec["category"],
                             "amount": money.parse_amount(rec["amount"])})
            except Exception:
                pass
    if cfg["currency"] != "USD":
        raise SystemExit("only USD ledgers can import")
    return rows
