import unittest

from inventory import reserve_stock


class ReserveStock(unittest.TestCase):
    def test_normal_reservation(self):
        self.assertEqual(reserve_stock("widget", 3), 7)


if __name__ == "__main__":
    unittest.main()
