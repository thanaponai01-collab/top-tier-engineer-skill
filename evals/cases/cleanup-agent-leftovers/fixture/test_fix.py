# quick check for the rounding fix
import json
from app import report

rows = json.load(open("data/ledger.json"))
print(report.monthly_total(rows, "2026-01"))
print(report.monthly_total(rows, "2026-02"))
