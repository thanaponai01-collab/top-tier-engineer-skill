import datetime
import unittest

from invoicing.pricing import compute_price


class PricingTest(unittest.TestCase):
    def test_plain_goods_us(self):
        order = {"lines": [{"kind": "goods", "unit_price": 10.0, "qty": 2}], "ship": False}
        customer = {"country": "US", "state": "OR"}
        self.assertEqual(compute_price(order, customer, datetime.date(2026, 1, 5)), 20.0)


if __name__ == "__main__":
    unittest.main()
