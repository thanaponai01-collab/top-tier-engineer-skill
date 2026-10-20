import unittest

from discount import discount_pct


class DiscountTest(unittest.TestCase):
    def test_under_threshold(self):
        self.assertEqual(discount_pct(99), 0)

    def test_boundary(self):
        self.assertEqual(discount_pct(100), 0)

    def test_large(self):
        self.assertEqual(discount_pct(500), 10)
