import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class OrdersTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        os.environ["SHOP_DB"] = os.path.join(self.tmp.name, "test.db")
        subprocess.run([sys.executable, "migrate.py", "up"], cwd=ROOT, check=True, capture_output=True)

    def tearDown(self):
        del os.environ["SHOP_DB"]
        self.tmp.cleanup()

    def test_create_and_read(self):
        from app import orders
        oid = orders.create_order("alice", 19.99)
        self.assertEqual(orders.get_order(oid)["customer"], "alice")
        self.assertEqual(orders.order_line(orders.get_order(oid)), f"#{oid} alice: $19.99")

    def test_full_refund(self):
        from app import orders
        oid = orders.create_order("bob", 10.0)
        self.assertEqual(orders.refund(oid, 10.0), 0)
        self.assertEqual(orders.get_order(oid)["status"], "refunded")

    def test_refund_more_than_order(self):
        from app import orders
        oid = orders.create_order("bob", 5.0)
        with self.assertRaises(ValueError):
            orders.refund(oid, 6.0)

    def test_invoice_totals(self):
        from app import orders
        from worker import invoices
        orders.create_order("carol", 1.10)
        orders.create_order("carol", 2.20)
        day = __import__("datetime").datetime.utcnow().strftime("%Y-%m-%d")
        self.assertEqual(invoices.invoice_totals(day), {"carol": 3.30})


if __name__ == "__main__":
    unittest.main()
