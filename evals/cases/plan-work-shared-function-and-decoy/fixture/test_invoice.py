import unittest

from data import ACME, HANS, SOMCHAI
from invoice import subtotal, total
from models import Invoice, Line


class Totals(unittest.TestCase):
    def test_subtotal_adds_lines(self):
        inv = Invoice("t", SOMCHAI, [Line("a", 2, 100), Line("b", 1, 50)])
        self.assertEqual(subtotal(inv), 250)

    def test_thai_tax_is_seven_percent(self):
        inv = Invoice("t", SOMCHAI, [Line("a", 1, 10000)])
        self.assertEqual(total(inv), 10700)

    def test_us_invoice_carries_no_tax(self):
        inv = Invoice("t", ACME, [Line("a", 1, 10000)])
        self.assertEqual(total(inv), 10000)

    def test_german_tax_is_nineteen_percent(self):
        inv = Invoice("t", HANS, [Line("a", 1, 10000)])
        self.assertEqual(total(inv), 11900)


if __name__ == "__main__":
    unittest.main()
