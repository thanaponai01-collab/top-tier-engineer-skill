import unittest
from commerce import discount

class DiscountTest(unittest.TestCase):
    def test_discount(self):
        self.assertEqual(discount(100), 10, "discount mismatch")
        self.assertEqual(discount(101), 10, "discount mismatch")

    def test_below_threshold(self):
        for total in (49, 50, 99):
            self.assertEqual(discount(total), 0, "discount mismatch")
