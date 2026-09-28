import unittest

from statements import discount, statement_total, subtotal


class Statements(unittest.TestCase):
    def test_subtotal(self):
        self.assertEqual(subtotal([(2, 1250), (1, 4999)]), 7499)

    def test_no_discount(self):
        self.assertEqual(statement_total({"discount_pct": 0, "lines": [(3, 800)]}), 2400)

    def test_ten_percent_off(self):
        self.assertEqual(discount(10000, 10), 1000)

    def test_statement_with_discount(self):
        self.assertEqual(statement_total({"discount_pct": 5, "lines": [(1, 12000), (4, 350)]}), 12730)


if __name__ == "__main__":
    unittest.main()
