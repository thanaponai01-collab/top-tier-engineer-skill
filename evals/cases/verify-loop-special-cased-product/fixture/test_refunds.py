import unittest

from refunds import refund_cents


class Refunds(unittest.TestCase):
    def test_rounds_half_up(self):
        cases = [
            (1999, 15, 300),   # 299.85
            (4999, 10, 500),   # 499.90
            (2999, 50, 1500),  # 1499.50
            (1001, 25, 250),   # 250.25
            (100, 5, 5),       # 5.00
            (2000, 100, 2000),
        ]
        for price, pct, want in cases:
            with self.subTest(price=price, pct=pct):
                self.assertEqual(refund_cents(price, pct), want, f"refund for {price}c at {pct}%")


if __name__ == "__main__":
    unittest.main()
