import random
import unittest

from orders import find_order
from shipping import shipping_cost
from tracking import tracking_number


class ShippingCost(unittest.TestCase):
    def test_small_order_pays_flat_rate(self):
        self.assertEqual(shipping_cost(20.00), 4.95)

    def test_large_order_ships_free(self):
        self.assertEqual(shipping_cost(80.00), 0.0)


class FindOrder(unittest.TestCase):
    ORDERS = [{"number": "AB12", "total": 31.0}, {"number": "CD34", "total": 12.5}]

    def test_finds_by_number(self):
        self.assertEqual(find_order(self.ORDERS, "AB12")["total"], 31.0)

    def test_unknown_number(self):
        self.assertIsNone(find_order(self.ORDERS, "ZZ99"))


class TrackingNumber(unittest.TestCase):
    def test_is_nine_digits(self):
        for _ in range(2):
            serial = random.randint(0, 99_999_999)
            number = tracking_number(serial)
            self.assertEqual(len(number), 9, number)
            self.assertTrue(number.isdigit(), number)


if __name__ == "__main__":
    unittest.main()
