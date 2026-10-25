import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from orders.model import Line, Order  # noqa: E402


def order():
    return Order("T-1", "test", [Line("L1", "A", 250, 2), Line("L2", "B", 1000, 1)])


class OrderTotal(unittest.TestCase):
    def test_total_sums_lines(self):
        self.assertEqual(order().total, 1500)

    def test_add_line_counts(self):
        o = order()
        o.add_line(Line("L3", "C", 5, 3))
        self.assertEqual(o.total, 1515)

    def test_round_trip(self):
        o = order()
        self.assertEqual(Order.from_dict(o.to_dict()).total, 1500)


class Cli(unittest.TestCase):
    def test_list_runs(self):
        out = subprocess.run([sys.executable, "shop.py", "list"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout
        self.assertIn("A-1001", out)


if __name__ == "__main__":
    unittest.main()
