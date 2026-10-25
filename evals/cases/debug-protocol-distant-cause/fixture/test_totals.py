import unittest

from totals import total


class Totals(unittest.TestCase):
    def test_adds_rows(self):
        self.assertEqual(total([{"amount": 10}, {"amount": 20}]), 30)

    def test_empty(self):
        self.assertEqual(total([]), 0)


if __name__ == "__main__":
    unittest.main()
