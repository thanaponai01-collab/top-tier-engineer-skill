import unittest
from payout import calculate_payout


class PayoutTest(unittest.TestCase):
    def test_payout_deducts_fee(self):
        self.assertEqual(calculate_payout([500, 300], 50), 750, "payout fee deduction mismatch")

    def test_payout_zero_floor(self):
        self.assertEqual(calculate_payout([100], 200), 0)


if __name__ == "__main__":
    unittest.main()
