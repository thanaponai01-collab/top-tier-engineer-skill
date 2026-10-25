import unittest

import app
import db


def login(name, pw):
    status, body = app.handle("POST", "/login", body={"username": name, "password": pw})
    return {"Authorization": "Bearer " + body["token"]}


class Shop(unittest.TestCase):
    def setUp(self):
        db.reset()

    def test_catalog_is_public(self):
        self.assertEqual(app.handle("GET", "/catalog")[0], 200)

    def test_customer_sees_own_invoice(self):
        status, body = app.handle("GET", "/invoices/100", login("alice", "alice-pw"))
        self.assertEqual((status, body["amount"]), (200, 42.50))

    def test_customer_cannot_see_others_invoice(self):
        self.assertEqual(app.handle("GET", "/invoices/101", login("alice", "alice-pw"))[0], 403)

    def test_order_paid_from_credit(self):
        h = login("bob", "bob-pw")
        status, body = app.handle("POST", "/orders", h, {"items": [{"sku": "gizmo", "qty": 1}]})
        self.assertEqual((status, body["total"]), (201, 4.50))
        self.assertAlmostEqual(db.USERS["bob"].credit, 0.50)

    def test_order_over_credit_refused(self):
        h = login("bob", "bob-pw")
        self.assertEqual(app.handle("POST", "/orders", h, {"items": [{"sku": "gadget", "qty": 1}]})[0], 403)

    def test_export_own(self):
        status, body = app.handle("POST", "/invoices/export", login("alice", "alice-pw"))
        self.assertIn("100,42.50", body)

    def test_refund_staff_only(self):
        with self.assertRaises(PermissionError):
            app.r_refund(login("bob", "bob-pw"), {}, ["101"])
        self.assertEqual(app.r_refund(login("sam", "sam-pw"), {}, ["101"])[0], 200)

    def test_signup_and_login(self):
        self.assertEqual(app.handle("POST", "/signup", body={"username": "carol", "password": "x"})[0], 201)
        login("carol", "x")


if __name__ == "__main__":
    unittest.main()
