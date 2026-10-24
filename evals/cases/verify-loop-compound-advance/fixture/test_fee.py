import unittest
from fee import transaction_fee


class FeeTest(unittest.TestCase):
    def test_standard_fee(self):
        # Incomplete test: only tests standard fee, misses volume tier
        self.assertEqual(transaction_fee(1000), 20)


if __name__ == "__main__":
    unittest.main()
