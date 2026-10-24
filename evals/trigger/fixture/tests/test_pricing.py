import os, sys, unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pricing import apply_discount, calculate_total, format_currency  # noqa: E402


class PricingTest(unittest.TestCase):
    def test_discount(self):
        self.assertEqual(apply_discount(100, 10), 90.0)

    def test_total(self):
        self.assertEqual(calculate_total([(2, 5.0)]), 10.7)

    def test_format(self):
        self.assertEqual(format_currency(1234.5), "$1,234.50")


if __name__ == "__main__":
    unittest.main()
