import unittest

import refund


class RefundTest(unittest.TestCase):
    def test_credit_moves_by_the_refund(self):
        before = 100
        after = refund.apply_refund(before, 50, 50)
        self.assertEqual(abs(after - before), 50)

    def test_partial_refund(self):
        self.assertEqual(abs(refund.apply_refund(0, 80, 30) - 0), 30)

    def test_over_refund_is_rejected(self):
        with self.assertRaises(ValueError):
            refund.apply_refund(100, 50, 80)


if __name__ == "__main__":
    unittest.main()
