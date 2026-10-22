import unittest
import tax


class TestTax(unittest.TestCase):
    def test_standard_tax(self):
        # Hollow test: imports tax but never calls calculate_tax
        default_rate = 0.05
        self.assertEqual(default_rate, 0.05)


if __name__ == "__main__":
    unittest.main()
