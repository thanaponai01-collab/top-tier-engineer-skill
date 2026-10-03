"""An old suite, intentionally insufficient for the acceptance requirement."""
import unittest
from app import total


class Totals(unittest.TestCase):
    def test_returns_a_positive_number(self):
        self.assertGreater(total(), 0)


if __name__ == "__main__":
    unittest.main()
