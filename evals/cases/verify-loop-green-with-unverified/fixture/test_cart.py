import unittest

from cart import cart_total


class CartTest(unittest.TestCase):
    def test_total(self):
        self.assertEqual(cart_total([(5, 2), (3, 1)]), 13)
