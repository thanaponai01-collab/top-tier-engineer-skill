import unittest

import db
from report import customer_totals, recent_orders


class Report(unittest.TestCase):
    def setUp(self):
        self.conn = db.build()
        db.seed(self.conn, n_customers=50, orders_per_customer=4)

    def test_customer_totals_sums_each_customer(self):
        totals = customer_totals(self.conn)
        self.assertEqual(len(totals), 50)
        self.assertAlmostEqual(totals["customer-1"], 10.0 + 11.0 + 12.0 + 13.0)

    def test_recent_orders_is_newest_first_and_bounded(self):
        rows = recent_orders(self.conn, limit=5)
        self.assertEqual(len(rows), 5)
        dates = [r[3] for r in rows]
        self.assertEqual(dates, sorted(dates, reverse=True))


if __name__ == "__main__":
    unittest.main()
