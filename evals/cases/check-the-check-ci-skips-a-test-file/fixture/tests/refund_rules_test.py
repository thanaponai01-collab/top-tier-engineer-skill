import unittest

from shop.refunds import refund


class RefundRulesTest(unittest.TestCase):
    def test_first_refund(self):
        self.assertEqual(refund(paid=8000, already_refunded=0, amount=3000), 3000)

    def test_refund_everything(self):
        self.assertEqual(refund(paid=8000, already_refunded=0, amount=8000), 8000)

    def test_second_refund_within_what_is_left(self):
        self.assertEqual(refund(paid=8000, already_refunded=3000, amount=5000), 8000)

    def test_second_refund_cannot_exceed_what_is_left(self):
        with self.assertRaises(ValueError):
            refund(paid=8000, already_refunded=3000, amount=6000)

    def test_zero_refund_rejected(self):
        with self.assertRaises(ValueError):
            refund(paid=8000, already_refunded=0, amount=0)
