"""Grader: the four planted bugs are fixed and nothing the shop relies on changed.

Dropped into the agent's finished repo as tests/test_hidden.py and run alone, the same way for
both arms.
"""
import unittest

from printshop import jobs, notify, orders, stock
from printshop.models import Customer, Order, OrderError
from printshop.printer import PrintJob, PrinterError


class FakePrinter:
    def __init__(self, fail=0):
        self.fail = fail
        self.sent = []

    def send(self, oid, pages):
        if self.fail:
            self.fail -= 1
            raise PrinterError("paper jam")
        self.sent.append((oid, pages))


def paid(oid="H1", pages=10):
    o = Order(oid, "ann", pages, 0)
    orders.checkout(o)
    orders.pay(o, 5)
    return o


class Fixed(unittest.TestCase):
    def setUp(self):
        stock.reset()

    def test_paid_then_cancelled_order_can_be_refunded(self):
        o = paid()
        orders.cancel(o)
        orders.refund(o)
        self.assertTrue(o.refunded)

    def test_nightly_job_expires_an_unpaid_checked_out_order(self):
        o = Order("H2", "bob", 40, 0)
        orders.checkout(o)
        self.assertEqual(stock.available(), 960)
        self.assertEqual(jobs.expire_unpaid([o], 2 * 24 * 3600), ["H2"])
        self.assertEqual(o.status, "cancelled")
        self.assertEqual(stock.available(), 1000)

    def test_nightly_job_leaves_a_fresh_unpaid_order(self):
        o = Order("H3", "bob", 40, 0)
        orders.checkout(o)
        self.assertEqual(jobs.expire_unpaid([o], 60), [])
        self.assertEqual(o.status, "awaiting_payment")

    def test_printer_works_again_after_a_jam(self):
        job = PrintJob(FakePrinter(fail=1))
        a, b = paid("H4"), paid("H5")
        self.assertFalse(orders.start_print(a, job))
        self.assertEqual(a.status, "paid")
        self.assertFalse(job.printing)
        self.assertTrue(orders.start_print(b, job))
        self.assertEqual(job.describe(), "finished")

    def test_cancelled_order_cannot_ship(self):
        o = paid("H6")
        orders.cancel(o)
        with self.assertRaises(OrderError):
            orders.ship(o)

    def test_unpaid_order_cannot_ship(self):
        o = Order("H7", "cy", 1, 0)
        orders.checkout(o)
        with self.assertRaises(OrderError):
            orders.ship(o)


class Unchanged(unittest.TestCase):
    def setUp(self):
        stock.reset()

    def test_happy_path(self):
        o = paid("U1")
        job = PrintJob(FakePrinter())
        self.assertTrue(orders.start_print(o, job))
        orders.ship(o)
        orders.archive(o)
        self.assertEqual(o.status, "archived")

    def test_archive_still_needs_shipped(self):
        with self.assertRaises(OrderError):
            orders.archive(paid("U2"))

    def test_unpaid_cancelled_order_still_not_refundable(self):
        o = Order("U3", "bob", 5, 0)
        orders.checkout(o)
        orders.cancel(o)
        with self.assertRaises(OrderError):
            orders.refund(o)

    def test_refund_once(self):
        o = paid("U4")
        orders.cancel(o)
        orders.refund(o)
        with self.assertRaises(OrderError):
            orders.refund(o)

    def test_every_notify_combination_is_allowed(self):
        c = Customer("ann", email="a@x", phone="555")
        for e in (True, False):
            for s in (True, False):
                c.set_prefs(e, s)
                kinds = [k for k, _ in notify.channels(c)]
                self.assertEqual(kinds, [k for k, on in (("email", e), ("sms", s)) if on])

    def test_printing_cannot_be_cancelled(self):
        o = paid("U5")
        o.status = "printing"
        with self.assertRaises(OrderError):
            orders.cancel(o)


if __name__ == "__main__":
    unittest.main()
