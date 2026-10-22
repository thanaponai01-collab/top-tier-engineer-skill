import unittest

from shipping import order_total, shipping_cost


class ShippingCostTest(unittest.TestCase):
    def test_small_order_pays_standard(self):
        self.assertEqual(shipping_cost(12.00, 1), 4.99)

    def test_just_under_free_shipping(self):
        self.assertEqual(shipping_cost(49.99, 1), 4.99)

    def test_just_over_free_shipping(self):
        self.assertEqual(shipping_cost(50.01, 1), 0.0)

    def test_heavy_parcel_adds_fee(self):
        self.assertEqual(shipping_cost(12.00, 25), 19.99)

    def test_light_parcel_has_no_fee(self):
        self.assertEqual(shipping_cost(12.00, 19.5), 4.99)

    def test_heavy_fee_on_free_order(self):
        self.assertEqual(shipping_cost(80.00, 30), 15.00)

    def test_express_on_small_order(self):
        self.assertEqual(shipping_cost(12.00, 1, express=True), 12.49)

    def test_express_on_free_order(self):
        self.assertEqual(shipping_cost(80.00, 1, express=True), 7.50)


class OrderTotalTest(unittest.TestCase):
    def test_small_order_total(self):
        self.assertEqual(order_total(12.00, 1), 17.95)

    def test_free_shipping_total(self):
        self.assertEqual(order_total(100.00, 1), 108.00)

    def test_shipping_is_not_taxed(self):
        self.assertEqual(order_total(12.00, 25), 32.95)


if __name__ == "__main__":
    unittest.main()
