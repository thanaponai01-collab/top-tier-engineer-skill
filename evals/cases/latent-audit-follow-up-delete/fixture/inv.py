"""inv: a small inventory CLI."""
import argparse, sys

from app import store
from app.exporters import load_exporter
from app.jobs import run_all, run_one
from app.report import summary

FORMATS = ("csv", "json", "xml", "yaml", "md", "html", "tsv")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="inv")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add", help="add an item")
    a.add_argument("name")
    a.add_argument("qty", type=int)
    sub.add_parser("list", help="list items")
    e = sub.add_parser("export", help="export items")
    e.add_argument("fmt", choices=FORMATS)
    sub.add_parser("stats", help="stock summary")
    sub.add_parser("run-jobs", help="run the scheduled jobs once")
    j = sub.add_parser("run-job", help="run one job by name")
    j.add_argument("name")
    args = ap.parse_args(argv)

    items = store.load()
    if args.cmd == "add":
        item = store.add(items, args.name, args.qty)
        store.save(items)
        print(f"added #{item['id']} {item['name']}")
    elif args.cmd == "list":
        for it in items:
            print(f"#{it['id']} {it['name']} x{it['qty']}")
    elif args.cmd == "export":
        sys.stdout.write(load_exporter(args.fmt)(items))
    elif args.cmd == "stats":
        print(summary(items))
    elif args.cmd == "run-job":
        print(run_one(args.name, items))
    elif args.cmd == "run-jobs":
        for line in run_all(items):
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
