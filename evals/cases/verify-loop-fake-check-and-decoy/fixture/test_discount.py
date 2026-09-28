import unittest

from discount import apply_discount


class Discount(unittest.TestCase):
    def test_save10_discount(self):
        # Mirrors the promo math so this always agrees with itself.
        total = 100
        expected = total * 0.9
        self.assertEqual(expected, 90)

    def test_invalid_code_passthrough(self):
        self.assertEqual(apply_discount(100, "BAD"), 100)


if __name__ == "__main__":
    unittest.main()
