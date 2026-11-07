"""Budget CLI. Commands: list, add, report MONTH, export FORMAT, import CSV, migrate."""
import sys
from importlib import import_module

from app import config, export, importer, money, report, store

USAGE = "usage: budget.py list | add AMOUNT CATEGORY DATE | report YYYY-MM | export FORMAT | import CSV | migrate"


def main(argv):
    if not argv:
        print(USAGE)
        return 1
    cmd, *rest = argv
    cfg = config.load_config()
    rows = store.load(cfg["data"])
    if cmd == "list":
        for row in rows:
            print(f"{row['date']}  {row['category']:<12} {money.format_money(row['amount'])}")
    elif cmd == "add":
        amount, category, date = rest
        rows.append({"date": date, "category": category, "amount": money.parse_amount(amount)})
        store.save(cfg["data"], rows)
        print("added")
    elif cmd == "report":
        print(f"{rest[0]}: {money.format_money(report.monthly_total(rows, rest[0]))}")
        for category, cents in report.by_category(rows, rest[0]):
            print(f"  {category:<12} {money.format_money(cents)}")
    elif cmd == "export":
        print(export.export(rows, rest[0]))
    elif cmd == "import":
        added = importer.import_csv(rest[0])
        store.save(cfg["data"], rows + added)
        print(f"imported {len(added)} rows")
    elif cmd == "migrate":
        step = import_module(f"app.{cfg['migration']}")
        store.save(cfg["data"], step.migrate(rows))
        print(f"migrated with {cfg['migration']}")
    else:
        print(USAGE)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
