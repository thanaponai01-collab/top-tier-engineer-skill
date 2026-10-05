import unittest
from commerce import shipping_fee

class ShippingTest(unittest.TestCase):
    def test_shipping(self):
        self.assertEqual(shipping_fee(50), 0, "shipping fee mismatch")
        self.assertEqual(shipping_fee(49), 5, "shipping fee mismatch")
