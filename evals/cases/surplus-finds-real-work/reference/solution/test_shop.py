import unittest

from loyalty import points_for, tier
from money import format_price
from returns import can_return
from tax import vat


class Loyalty(unittest.TestCase):
    def test_new_customer_is_member(self):
        self.assertEqual(tier(40), "member")

    def test_regular_is_silver(self):
        self.assertEqual(tier(600), "silver")

    def test_big_spender_is_gold(self):
        self.assertEqual(tier(4200), "gold")

    def test_thresholds_are_inclusive(self):
        self.assertEqual(tier(249), "member")
        self.assertEqual(tier(250), "silver")
        self.assertEqual(tier(999), "silver")
        self.assertEqual(tier(1000), "gold")

    def test_points_are_whole_euros(self):
        self.assertEqual(points_for(19.99), 19)


class Returns(unittest.TestCase):
    def test_recent_unopened(self):
        self.assertTrue(can_return(5, opened=False))

    def test_last_day_of_window(self):
        self.assertTrue(can_return(30, opened=False))
        self.assertFalse(can_return(31, opened=False))

    def test_too_late(self):
        self.assertFalse(can_return(45, opened=False))

    def test_opened(self):
        self.assertFalse(can_return(5, opened=True))


class Tax(unittest.TestCase):
    def test_sweden(self):
        self.assertEqual(vat(100, "SE"), 25.0)

    def test_finland_rounds_to_cents(self):
        self.assertEqual(vat(9.99, "FI"), 2.55)

    def test_unknown_country_is_an_error(self):
        with self.assertRaises(KeyError):
            vat(10, "XX")


class Money(unittest.TestCase):
    def test_thousands_separator(self):
        self.assertEqual(format_price(1234.5), "1,234.50 EUR")

    def test_other_currency(self):
        self.assertEqual(format_price(3, "SEK"), "3.00 SEK")


if __name__ == "__main__":
    unittest.main()
