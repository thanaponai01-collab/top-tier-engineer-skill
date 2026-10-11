import unittest

import api
import store
from billing import invoices


class Billing(unittest.TestCase):
    def setUp(self):
        store.INVOICES.clear(); store.CREDIT_NOTES.clear(); store.OUTBOX.clear()

    def test_send_once(self):
        i = api.create("acme", [("widget", 2, 10)])
        self.assertTrue(api.send(i))
        self.assertFalse(api.send(i))
        self.assertEqual(len(store.OUTBOX), 1)

    def test_sent_invoice_immutable(self):
        i = api.create("acme", [("widget", 2, 10)])
        api.send(i)
        with self.assertRaises(invoices.AlreadySent):
            invoices.edit(i, [("widget", 1, 10)])

    def test_credit_note(self):
        i = api.create("acme", [("widget", 2, 10)])
        api.send(i)
        n = api.correct(i, "wrong qty")
        self.assertEqual(store.CREDIT_NOTES[n]["amount"], -20)
        self.assertEqual(invoices.total(store.INVOICES[i]), 20)


if __name__ == "__main__":
    unittest.main()
