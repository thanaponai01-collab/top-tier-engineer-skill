import unittest
from coupons import apply_coupon


class TestCoupons(unittest.TestCase):
    def test_standard_discount(self):
        self.assertEqual(apply_coupon(1000, 200), 800)


if __name__ == "__main__":
    unittest.main()
