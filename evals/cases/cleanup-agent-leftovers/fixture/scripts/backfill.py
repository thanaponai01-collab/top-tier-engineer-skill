"""Fill a missing category with 'other'. See README: run once after upgrading old ledgers."""
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "data/ledger.json"
with open(path, encoding="utf-8") as fh:
    rows = json.load(fh)
for row in rows:
    row.setdefault("category", "other")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(rows, fh, indent=2)
print(f"backfilled {len(rows)} rows")
