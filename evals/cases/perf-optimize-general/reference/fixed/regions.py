"""Region names and tax rates, from data/regions.csv."""
import csv
import functools
import os
from decimal import Decimal

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "regions.csv")


@functools.lru_cache(maxsize=None)
def _table():
    with open(PATH, newline="", encoding="utf-8") as fh:
        return {row["code"]: row for row in csv.DictReader(fh)}


def tax_rate(code):
    return Decimal(_table()[code]["tax"])


def name(code):
    return _table()[code]["name"]
