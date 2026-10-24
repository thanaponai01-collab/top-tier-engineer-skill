import unittest
from fee import transaction_fee


class FeeTest(unittest.TestCase):
    def test_standard_fee(self):
        self.assertEqual(transaction_fee(1000), 10, "fee calculation mismatch")

    def test_volume_tier_fee(self):
        self.assertEqual(transaction_fee(200000), 4000, "fee calculation mismatch")


if __name__ == "__main__":
    unittest.main()
