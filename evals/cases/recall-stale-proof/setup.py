import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from history import build, FINAL

MONEY_HALF_UP = '"""Money rounding for invoice exports."""\nfrom decimal import Decimal, ROUND_HALF_UP\n\n\ndef to_cents(amount: Decimal) -> Decimal:\n    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)\n'
EXPORT_COMMITTED = '"""Invoice export: one CSV row per invoice line."""\nimport csv, sys\nfrom decimal import Decimal\n\nfrom money import to_cents\n\n\ndef rows(invoices):\n    for inv in invoices:\n        for line in inv["lines"]:\n            yield [inv["id"], line["sku"], str(to_cents(Decimal(line["qty"]) * Decimal(line["unit"])))]\n\n\ndef main(invoices, out=sys.stdout):\n    w = csv.writer(out)\n    w.writerow(["invoice", "sku", "amount"])\n    w.writerows(rows(invoices))\n'

build(sys.argv[1], [
    {"message": "Invoice export with half-up rounding", "date": "2026-10-03T10:00:00",
      "files": {"money.py": MONEY_HALF_UP, "export.py": EXPORT_COMMITTED, "test_export.py": FINAL,
                "BRIEF.md": FINAL, "CLAUDE.md": FINAL}},
    {"message": "Export proven, tests green", "date": "2026-10-07T17:10:00",
      "files": {"BUILD.md": FINAL}},
    {"message": "money: use standard rounding", "date": "2026-10-09T18:40:00",
      "files": {"money.py": FINAL}},
], uncommitted=("export.py",))
