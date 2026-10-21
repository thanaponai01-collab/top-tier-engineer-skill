import unittest

from pricing import order_total


class OrderTotalTest(unittest.TestCase):
    def test_sum_of_lines(self):
        self.assertEqual(order_total([(2, 250), (1, 99)]), 599)

    def test_discount_applies_to_the_subtotal(self):
        self.assertAlmostEqual(order_total([(1, 105), (1, 105)], 10), 189, delta=2)

    def test_rounds_half_up(self):
        self.assertAlmostEqual(order_total([(1, 5)], 10), 5, delta=2)

    def test_bulk_tier(self):
        self.assertEqual(order_total([(10, 100)]), 950)


if __name__ == "__main__":
    unittest.main()
