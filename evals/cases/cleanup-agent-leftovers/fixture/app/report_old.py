from collections import defaultdict


def monthly_total(rows, month):
    total = 0
    for row in rows:
        if row["date"][:7] == month:
            total += row["amount"]
    return total


def by_category(rows, month):
    totals = defaultdict(int)
    for row in rows:
        if row["date"][:7] == month:
            totals[row["category"]] += row["amount"]
    return list(totals.items())
