"""Nightly sales report: revenue by region with tax, and the top customers.

    python report.py data/orders.csv
"""
import csv
import sys
from decimal import Decimal

import regions
from layout import table


def load(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def dedupe(rows):
    """The export retries, so an order can appear more than once. The first row wins."""
    return list({row["order_id"]: row for row in rows}.values())


def by_region(rows):
    totals = {}
    for row in rows:
        code = row["region"]
        gross = Decimal(row["amount"]) * (1 + regions.tax_rate(code))
        totals[code] = totals.get(code, Decimal("0")) + gross
    return {regions.name(code): total.quantize(Decimal("0.01")) for code, total in totals.items()}


def top_customers(rows, n=5):
    spend = {}
    for row in rows:
        spend[row["email"]] = spend.get(row["email"], Decimal("0")) + Decimal(row["amount"])
    return sorted(spend.items(), key=lambda kv: (-kv[1], kv[0]))[:n]


def main(path):
    rows = dedupe(load(path))
    print(f"{len(rows)} orders")
    print()
    print(table(["region", "revenue"], sorted(by_region(rows).items())))
    print()
    print(table(["customer", "spend"], top_customers(rows)))


if __name__ == "__main__":
    main(sys.argv[1])
