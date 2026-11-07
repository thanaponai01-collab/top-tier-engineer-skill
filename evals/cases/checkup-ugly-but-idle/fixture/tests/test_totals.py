import unittest

from shop.cart import cart_total
from shop.receipt import receipt_total


class Totals(unittest.TestCase):
    def test_member_discount(self):
        self.assertEqual(cart_total([("mug", 1)], member=True), 1080)

    def test_receipt_matches_cart(self):
        items = [("tee", 3), ("cap", 2)]
        self.assertEqual(receipt_total(items, True), cart_total(items, True))


if __name__ == "__main__":
    unittest.main()
