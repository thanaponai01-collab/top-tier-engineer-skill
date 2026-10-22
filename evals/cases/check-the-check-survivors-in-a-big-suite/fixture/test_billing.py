import unittest

from billing import (annual_amount, apply_credit, invoice, late_interest, monthly_amount,
                     prorate, seat_price, split_payment)


class SeatPriceTest(unittest.TestCase):
    def test_list_prices(self):
        self.assertEqual(seat_price("starter", 1), 900)
        self.assertEqual(seat_price("team", 1), 2900)
        self.assertEqual(seat_price("business", 1), 7900)

    def test_nine_seats_pay_list(self):
        self.assertEqual(seat_price("team", 9), 2900)

    def test_ten_seats_get_five_percent(self):
        self.assertEqual(seat_price("team", 10), 2755)

    def test_twenty_five_seats_get_ten_percent(self):
        self.assertEqual(seat_price("team", 25), 2610)

    def test_forty_nine_seats_still_ten_percent(self):
        self.assertEqual(seat_price("team", 49), 2610)

    def test_fifty_seats_get_fifteen_percent(self):
        self.assertEqual(seat_price("team", 50), 2465)

    def test_discount_rounds_down(self):
        self.assertEqual(seat_price("starter", 50), 765)
        self.assertEqual(seat_price("business", 10), 7505)

    def test_unknown_plan(self):
        with self.assertRaises(ValueError):
            seat_price("enterprise", 3)

    def test_zero_seats(self):
        with self.assertRaises(ValueError):
            seat_price("team", 0)

    def test_one_seat_is_allowed(self):
        self.assertEqual(seat_price("starter", 1), 900)


class AmountTest(unittest.TestCase):
    def test_monthly(self):
        self.assertEqual(monthly_amount("team", 3), 8700)

    def test_annual_charges_ten_months(self):
        self.assertEqual(annual_amount("team", 3), 87000)


class ProrateTest(unittest.TestCase):
    def test_half_period(self):
        self.assertEqual(prorate(3000, 15, 30), 1500)

    def test_rounds_half_up(self):
        self.assertEqual(prorate(100, 1, 8), 13)

    def test_rounds_down_below_half(self):
        self.assertEqual(prorate(100, 1, 3), 33)

    def test_full_and_empty(self):
        self.assertEqual(prorate(3000, 30, 30), 3000)
        self.assertEqual(prorate(3000, 0, 30), 0)

    def test_out_of_range(self):
        with self.assertRaises(ValueError):
            prorate(3000, 31, 30)
        with self.assertRaises(ValueError):
            prorate(3000, -1, 30)


class CreditTest(unittest.TestCase):
    def test_credit_smaller_than_amount(self):
        self.assertEqual(apply_credit(5000, 1200), (3800, 0))

    def test_credit_larger_than_amount(self):
        self.assertEqual(apply_credit(5000, 8000), (0, 3000))

    def test_invoice_uses_credit(self):
        self.assertEqual(invoice("team", 3, credit=700), (8000, 0))

    def test_annual_invoice(self):
        self.assertEqual(invoice("starter", 2, annual=True), (18000, 0))


class SplitTest(unittest.TestCase):
    def test_even_split(self):
        self.assertEqual(split_payment(9000, 3), [3000, 3000, 3000])

    def test_one_card(self):
        self.assertEqual(split_payment(4321, 1), [4321])

    def test_parts_add_up(self):
        self.assertEqual(sum(split_payment(12000, 4)), 12000)

    def test_no_cards(self):
        with self.assertRaises(ValueError):
            split_payment(100, 0)


class LateInterestTest(unittest.TestCase):
    def test_within_grace(self):
        self.assertEqual(late_interest(50000, 3), 0)

    def test_last_grace_day(self):
        self.assertEqual(late_interest(50000, 7), 0)

    def test_after_grace(self):
        self.assertEqual(late_interest(50000, 10), 150)

    def test_rounds_down(self):
        self.assertEqual(late_interest(1999, 8), 1)


if __name__ == "__main__":
    unittest.main()
