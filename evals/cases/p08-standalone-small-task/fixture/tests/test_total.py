import unittest
from total import total

class TotalTests(unittest.TestCase):
    def test_total_includes_fee(self):
        self.assertEqual(total(10, 2), 12)

if __name__ == "__main__":
    unittest.main()
