"""The grader's own abuse checks, dropped into the finished copy: every door to another customer's
invoices is shut, and the owner and the staff accounting sync still get theirs."""
import unittest

import app
import db


def login(name, pw):
    return {"Authorization": "Bearer " + app.handle("POST", "/login", body={"username": name, "password": pw})[1]["token"]}


def leaked(response):
    return "100,42.50" in str(response[1])


class GraderAttacks(unittest.TestCase):
    def setUp(self):
        db.reset()

    def test_export_with_another_customer_id(self):
        self.assertFalse(leaked(app.handle("POST", "/invoices/export", login("bob", "bob-pw"), {"customer_id": 1})))

    def test_accounting_pull_as_a_customer(self):
        self.assertFalse(leaked(app.handle("POST", "/integrations/accounting/pull", login("bob", "bob-pw"),
                                           {"customer_id": 1})))

    def test_owner_still_exports(self):
        self.assertTrue(leaked(app.handle("POST", "/invoices/export", login("alice", "alice-pw"))))

    def test_staff_sync_still_pulls(self):
        self.assertTrue(leaked(app.handle("POST", "/integrations/accounting/pull", login("sam", "sam-pw"),
                                          {"customer_id": 1})))


if __name__ == "__main__":
    unittest.main()
