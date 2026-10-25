import csv

from store import db


def run(args):
    rows = db.load()
    with open(args[0], "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "customer", "amount", "paid"])
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} orders written to {args[0]}")
