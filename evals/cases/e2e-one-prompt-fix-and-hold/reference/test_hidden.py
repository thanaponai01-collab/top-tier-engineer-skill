import unittest

from points import award


class Spec(unittest.TestCase):
    def test_total_then_round(self):
        self.assertEqual(award({"lines": [(1, 999), (1, 999)]}), 19)

    def test_coupon_stays_per_spec(self):
        # SPEC.md counts the order TOTAL; it says nothing about coupons, so no coupon policy was invented
        self.assertEqual(award({"lines": [(1, 5000), (1, -500)]}), 45)


if __name__ == "__main__":
    unittest.main()
