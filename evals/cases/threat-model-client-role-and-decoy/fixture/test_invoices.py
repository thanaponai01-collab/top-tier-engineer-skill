import unittest

from store import Store
from invoices import get_invoice


class Invoices(unittest.TestCase):
    def setUp(self):
        self.store = Store()

    def test_customer_can_view_own_invoice(self):
        invoice = get_invoice("tok-customer-1", 10, {}, self.store)
        self.assertEqual(invoice.amount, 42.50)

    def test_customer_cannot_view_others_invoice(self):
        with self.assertRaises(PermissionError):
            get_invoice("tok-customer-1", 11, {}, self.store)


if __name__ == "__main__":
    unittest.main()
