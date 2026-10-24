import os, sys, unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from refunds import refund_amount  # noqa: E402


class RefundTest(unittest.TestCase):
    def test_refund_runs(self):
        self.assertIsInstance(refund_amount([(1, 10.0), (1, 5.0)], {1}), float)


if __name__ == "__main__":
    unittest.main()
