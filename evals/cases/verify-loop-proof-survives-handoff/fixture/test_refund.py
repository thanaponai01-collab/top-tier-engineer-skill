import unittest

import refund


class RefundTest(unittest.TestCase):
    def test_over_refund_is_rejected(self):
        with self.assertRaises(ValueError):
            refund.apply_refund(100, 50, 80)


if __name__ == "__main__":
    unittest.main()
