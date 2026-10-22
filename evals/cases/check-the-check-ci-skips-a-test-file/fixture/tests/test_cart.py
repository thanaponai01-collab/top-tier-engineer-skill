import unittest

from shop.cart import cart_total, line_total


class CartTest(unittest.TestCase):
    def test_line_total(self):
        self.assertEqual(line_total(3, 250), 750)

    def test_single_item(self):
        self.assertEqual(line_total(1, 999), 999)

    def test_zero_quantity_rejected(self):
        with self.assertRaises(ValueError):
            line_total(0, 250)

    def test_cart_total(self):
        self.assertEqual(cart_total([(2, 500), (1, 199)]), 1199)

    def test_empty_cart(self):
        self.assertEqual(cart_total([]), 0)
