import unittest

from printshop import notify, orders, stock
from printshop.models import Customer, Order, OrderError
from printshop.printer import PrintJob


class FakePrinter:
    def __init__(self):
        self.sent = []

    def send(self, oid, pages):
        self.sent.append((oid, pages))


class OrderFlow(unittest.TestCase):
    def setUp(self):
        stock.reset()

    def test_happy_path(self):
        o = Order("A1", "ann", 10, 0)
        orders.checkout(o)
        self.assertEqual(stock.available(), 990)
        orders.pay(o, 5)
        job = PrintJob(FakePrinter())
        self.assertTrue(orders.start_print(o, job))
        self.assertEqual(job.describe(), "finished")
        orders.ship(o)
        orders.archive(o)
        self.assertEqual(o.status, "archived")

    def test_cannot_pay_twice(self):
        o = Order("A2", "ann", 1, 0)
        orders.checkout(o)
        orders.pay(o, 5)
        with self.assertRaises(OrderError):
            orders.pay(o, 6)

    def test_cancel_returns_paper(self):
        o = Order("A3", "bob", 50, 0)
        orders.checkout(o)
        orders.cancel(o)
        self.assertEqual(stock.available(), 1000)
        self.assertEqual(o.status, "cancelled")

    def test_unpaid_order_cannot_be_refunded(self):
        o = Order("A4", "bob", 5, 0)
        orders.checkout(o)
        orders.cancel(o)
        with self.assertRaises(OrderError):
            orders.refund(o)

    def test_archive_needs_shipped(self):
        o = Order("A5", "cy", 5, 0)
        with self.assertRaises(OrderError):
            orders.archive(o)


class Notify(unittest.TestCase):
    def test_each_channel_on_its_own(self):
        c = Customer("ann", email="a@x", phone="555")
        c.set_prefs(True, False)
        self.assertEqual([k for k, _ in notify.channels(c)], ["email"])
        c.set_prefs(False, True)
        self.assertEqual([k for k, _ in notify.channels(c)], ["sms"])


if __name__ == "__main__":
    unittest.main()
