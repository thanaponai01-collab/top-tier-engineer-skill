import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ContactsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        os.environ["CRM_DB"] = os.path.join(self.tmp.name, "test.db")
        subprocess.run([sys.executable, "migrate.py", "up"], cwd=ROOT, check=True, capture_output=True)

    def tearDown(self):
        del os.environ["CRM_DB"]
        self.tmp.cleanup()

    def test_notes(self):
        from app import contacts
        cid = contacts.add_contact("Ada", "ada@example.com")
        contacts.add_note(cid, "met at the expo")
        contacts.add_note(cid, "wants a demo")
        self.assertEqual(contacts.get_contact(cid)["notes"], ["met at the expo", "wants a demo"])

    def test_v1_update(self):
        from api import v1
        from app import contacts
        cid = contacts.add_contact("Bo")
        status, body = v1.put(cid, {"email": "bo@example.com"})
        self.assertEqual((status, body["email"]), (200, "bo@example.com"))

    def test_export(self):
        from app import contacts
        from exports import csv_export
        contacts.add_contact("Cy", "cy@example.com")
        self.assertEqual(csv_export.export(os.path.join(self.tmp.name, "out.csv")), 1)


if __name__ == "__main__":
    unittest.main()
