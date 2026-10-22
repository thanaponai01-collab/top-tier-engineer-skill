import unittest
from datetime import date

from shop.coupons import apply_coupon

TODAY = date(2026, 5, 10)


class CouponTest(unittest.TestCase):
    def test_ten_percent(self):
        self.assertEqual(apply_coupon(5000, 10, date(2026, 6, 1), TODAY), 4500)

    def test_rounds_discount_down(self):
        self.assertEqual(apply_coupon(999, 15, date(2026, 6, 1), TODAY), 850)

    def test_expires_today_still_valid(self):
        self.assertEqual(apply_coupon(1000, 20, TODAY, TODAY), 800)

    def test_expired_rejected(self):
        with self.assertRaises(ValueError):
            apply_coupon(1000, 20, date(2026, 5, 9), TODAY)
