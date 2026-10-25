"""Reads the CSV into rows."""
import csv


def parse_amount(value):
    return int(float(value))


def load(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return [
            {"id": row["id"], "amount": parse_amount(row["amount"])}
            for row in csv.DictReader(fh)
        ]
