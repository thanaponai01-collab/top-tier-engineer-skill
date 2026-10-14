import unittest

from shop.cart import Cart
from shop.invoice import render


class CartTest(unittest.TestCase):
    def test_subtotal(self):
        c = Cart()
        c.add("MUG", 2)
        c.add("PIN")
        self.assertEqual(c.subtotal(), 2850)

    def test_unknown_sku(self):
        with self.assertRaises(ValueError):
            Cart().add("HAT")

    def test_invoice_total_line(self):
        c = Cart()
        c.add("TEE")
        self.assertIn("19.99", render(c).splitlines()[-1])


if __name__ == "__main__":
    unittest.main()
