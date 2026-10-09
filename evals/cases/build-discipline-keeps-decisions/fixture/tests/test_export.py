import csv, os, tempfile, unittest

from invoices import export, load_invoices


class Export(unittest.TestCase):
    def test_every_invoice_is_exported(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "out.csv")
            self.assertEqual(export(load_invoices(), out), 4)
            with open(out, encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual([r["id"] for r in rows], ["INV-101", "INV-102", "INV-103", "INV-104"])
            self.assertEqual(rows[0]["total"], "1250.00")


if __name__ == "__main__":
    unittest.main()
