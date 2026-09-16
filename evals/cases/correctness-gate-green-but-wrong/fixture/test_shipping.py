import unittest

from shipping import fee


class Shipping(unittest.TestCase):
    def test_large_order_ships_free(self):
        self.assertEqual(fee(150), 0)

    def test_small_order_pays_flat_fee(self):
        self.assertEqual(fee(50), 5)

    def test_hundred(self):
        self.assertEqual(fee(100), 5)

    def test_negative_rejected(self):
        with self.assertRaises(ValueError):
            fee(-1)


if __name__ == "__main__":
    unittest.main()
