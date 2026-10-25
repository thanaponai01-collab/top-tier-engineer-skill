import os
import sys
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import report  # noqa: E402
from layout import table  # noqa: E402


def order(oid, email="a@example.com", region="TY", amount="10.00"):
    return {"order_id": oid, "email": email, "region": region, "amount": amount, "date": "2026-10-01"}


class Report(unittest.TestCase):
    def test_dedupe_drops_a_repeated_order(self):
        rows = [order("A1"), order("A2"), order("A1")]
        self.assertEqual([r["order_id"] for r in report.dedupe(rows)], ["A1", "A2"])

    def test_by_region_adds_tax(self):
        rows = [order("A1", region="TY", amount="100.00"), order("A2", region="ON", amount="10.00")]
        self.assertEqual(report.by_region(rows), {"Tokyo": Decimal("110.00"), "Okinawa": Decimal("10.50")})

    def test_top_customers_by_spend(self):
        rows = [order("A1", "b@example.com", amount="5.00"), order("A2", "a@example.com", amount="7.00"),
                order("A3", "b@example.com", amount="4.00")]
        self.assertEqual(report.top_customers(rows, 1), [("b@example.com", Decimal("9.00"))])

    def test_table_pads_columns(self):
        self.assertEqual(table(["a", "bb"], [("x", 1)]), "a  bb\n-  --\nx   1")


if __name__ == "__main__":
    unittest.main()
