"""Weekly CSV for the sales team (`python -m exports.csv_export out.csv`), run by crm-export-cron."""
import csv
import sys

from app.db import connect

FIELDS = "id,name,email,notes".split(",")


def export(path):
    with connect() as conn:
        rows = conn.execute(f"SELECT {', '.join(FIELDS)} FROM contacts ORDER BY id").fetchall()
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(FIELDS)
        w.writerows([tuple(r) for r in rows])
    return len(rows)


if __name__ == "__main__":
    print(export(sys.argv[1]))
