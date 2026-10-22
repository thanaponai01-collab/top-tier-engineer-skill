import unittest

from points import points_for, redeem
from points_fixtures import PointsFixtures


class RedeemTest(unittest.TestCase):
    def test_redeem_lowers_balance(self):
        self.assertEqual(redeem(120, 20), 100)

    def test_overdraw_is_rejected(self):
        with self.assertRaises(ValueError):
            redeem(120, 121)


class PointsEarnedTest(PointsFixtures):
    def test_one_point_per_whole_dollar(self):
        self.assertEqual(points_for(42.99, self.regular["tier"]), 42)

    def test_gold_earns_double(self):
        self.assertEqual(points_for(42.99, self.gold["tier"]), 84)

    def test_regular_does_not_earn_double(self):
        self.assertNotEqual(points_for(42.99, self.regular["tier"]), 84)


if __name__ == "__main__":
    unittest.main()
