import io, unittest
from decimal import Decimal

import export
from money import to_cents


class ToCents(unittest.TestCase):
    def test_half_rounds_up(self):
        self.assertEqual(to_cents(Decimal("10.125")), Decimal("10.13"))

    def test_plain(self):
        self.assertEqual(to_cents(Decimal("3.1")), Decimal("3.10"))


class Export(unittest.TestCase):
    def test_header_and_rows(self):
        out = io.StringIO()
        export.main([{"id": "INV-1", "lines": [{"sku": "A", "qty": "3", "unit": "3.375"}]}], out)
        self.assertEqual(out.getvalue().splitlines(), ["invoice,sku,amount", "INV-1,A,10.13"])


if __name__ == "__main__":
    unittest.main()
