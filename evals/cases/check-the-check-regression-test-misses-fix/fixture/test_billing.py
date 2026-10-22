import unittest
from datetime import date

from billing import invoice_total, late_fee

DUE = date(2026, 3, 31)


class LateFeeTest(unittest.TestCase):
    def test_late_payment_is_charged(self):
        self.assertEqual(late_fee(DUE, date(2026, 4, 2), 200.0), 10.0)

    def test_early_payment_is_free(self):
        self.assertEqual(late_fee(DUE, date(2026, 3, 1), 200.0), 0.0)

    def test_due_date_is_not_late(self):
        # Regression test for #12: a customer who pays on the due date was charged a late fee.
        self.assertEqual(late_fee(DUE, DUE, 200.0), 0.0)


class InvoiceTotalTest(unittest.TestCase):
    def test_late_invoice_adds_fee(self):
        self.assertEqual(invoice_total(200.0, DUE, date(2026, 4, 2)), 210.0)

    def test_early_invoice_has_no_fee(self):
        self.assertEqual(invoice_total(200.0, DUE, date(2026, 3, 1)), 200.0)


if __name__ == "__main__":
    unittest.main()
