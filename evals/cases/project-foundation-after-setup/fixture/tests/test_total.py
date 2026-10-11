import unittest
from app import total


class TotalTest(unittest.TestCase):
    def test_fee(self):
        self.assertEqual(total(100), 110, "expected total 110")
