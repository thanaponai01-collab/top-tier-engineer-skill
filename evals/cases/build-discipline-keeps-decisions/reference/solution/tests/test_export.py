import json, os, tempfile, unittest

from invoices import export, load_invoices


class Export(unittest.TestCase):
    def exported(self, invoices):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "out.json")
            n = export(invoices, out)
            with open(out, encoding="utf-8") as fh:
                return n, json.load(fh)

    def test_every_invoice_is_exported_as_json(self):
        n, rows = self.exported(load_invoices())
        self.assertEqual(n, 4)
        self.assertEqual([r["id"] for r in rows], ["INV-101", "INV-102", "INV-103", "INV-104"])
        self.assertEqual(rows[0]["total"], "1250.00")

    def test_month_keeps_only_that_month(self):
        _, rows = self.exported(load_invoices("2026-09"))
        self.assertEqual([r["id"] for r in rows], ["INV-103", "INV-104"])


if __name__ == "__main__":
    unittest.main()
