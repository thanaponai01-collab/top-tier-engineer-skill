import unittest

from shop.gift_cards import spend


class GiftCardTest(unittest.TestCase):
    def test_spend_part(self):
        self.assertEqual(spend(5000, 1250), 3750)

    def test_spend_all(self):
        self.assertEqual(spend(5000, 5000), 0)

    def test_overspend_rejected(self):
        with self.assertRaises(ValueError):
            spend(5000, 5001)
