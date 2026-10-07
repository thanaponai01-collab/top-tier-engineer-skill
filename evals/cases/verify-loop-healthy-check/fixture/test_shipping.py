import unittest
from shipping import shipping_fee


class ShippingTest(unittest.TestCase):
    def test_boundary(self):
        self.assertEqual([shipping_fee(x) for x in (0, 49, 50, 51)], [5, 5, 0, 0])
