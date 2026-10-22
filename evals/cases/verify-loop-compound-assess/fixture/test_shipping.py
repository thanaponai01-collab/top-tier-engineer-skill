import unittest
from shipping import calculate_shipping


class TestShipping(unittest.TestCase):
    def test_under_threshold(self):
        self.assertEqual(calculate_shipping(4999), 500)

    def test_at_threshold(self):
        self.assertEqual(calculate_shipping(5000), 0)

    def test_over_threshold(self):
        self.assertEqual(calculate_shipping(10000), 0)


if __name__ == "__main__":
    unittest.main()
