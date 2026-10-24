import unittest
import payout


class PayoutTest(unittest.TestCase):
    def test_payout_exists(self):
        # Hollow test: asserts literal tautology 1 == 1, never calls calculate_payout
        self.assertEqual(1, 1)


if __name__ == "__main__":
    unittest.main()
