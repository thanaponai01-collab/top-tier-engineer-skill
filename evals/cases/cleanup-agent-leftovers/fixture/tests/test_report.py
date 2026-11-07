import json
import unittest

from app import report


def rows():
    with open("data/ledger.json", encoding="utf-8") as fh:
        return json.load(fh)


class Report(unittest.TestCase):
    def test_january_total_counts_the_refund(self):
        self.assertEqual(report.monthly_total(rows(), "2026-01"), 123456)

    def test_february_total(self):
        self.assertEqual(report.monthly_total(rows(), "2026-02"), 125560)

    def test_by_category(self):
        self.assertEqual(report.by_category(rows(), "2026-02"),
                         [("Food", 3310), ("Rent", 120000), ("Transport", 2250)])
