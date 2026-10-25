"""pantry: keep track of what's in the cupboard and what to buy."""
import argparse, csv, os, sys

import store


def cmd_add(args):
    item = store.add_item(args.name, args.qty, args.min, args.unit)
    print(f"added #{item['id']} {item['name']} ({item['qty']} {item['unit']})")


def cmd_list(args):
    data = store.load()
    items = store.search(data, args.q) if args.q else data["items"]
    if args.low:
        items = [i for i in items if i["qty"] < i["min"]]
    for i in items:
        print(f"#{i['id']:<3} {i['name']:<16} {i['qty']} {i['unit']} (min {i['min']})")


def cmd_use(args):
    item = store.use_item(args.id, args.n)
    print(f"{item['name']}: {item['qty']} {item['unit']} left")


def cmd_restock(args):
    item = store.restock(args.id, args.n)
    print(f"{item['name']}: {item['qty']} {item['unit']}")


def cmd_shop(args):
    for i in store.shopping_list(store.load()):
        print(f"- {i['name']}: buy {i['buy']} {i['unit']}")


def cmd_export(args):
    data = store.load()
    with open(args.path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["id", "name", "qty", "min", "unit"])
        writer.writeheader()
        writer.writerows(data["items"])
    print(f"wrote {len(data['items'])} items to {args.path}")


def cmd_import(args):
    with open(args.path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for row in rows:
        store.add_item(row["name"], int(row["quantity"]), int(row["min"]), row["unit"])
    print(f"imported {len(rows)} items")


def cmd_wipe(args):
    if not args.yes:
        print("this deletes every item and the usage log; rerun with --yes", file=sys.stderr)
        return 1
    store.save({"items": [], "used": []})
    with open(os.path.join(os.path.dirname(store.DB), "wipe.log"), "a", encoding="utf-8") as fh:
        fh.write("wiped\n")
    print("pantry wiped")


def cmd_serve(args):
    from web.server import serve
    serve(args.port)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pantry")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add", help="add an item")
    p.add_argument("name"); p.add_argument("qty", type=int)
    p.add_argument("--min", type=int, default=1); p.add_argument("--unit", default="pcs")
    p.set_defaults(fn=cmd_add)
    p = sub.add_parser("list", help="list items")
    p.add_argument("--low", action="store_true", help="only items below their minimum")
    p.add_argument("-q", help="only names containing this text")
    p.set_defaults(fn=cmd_list)
    p = sub.add_parser("use", help="use some of an item")
    p.add_argument("id", type=int); p.add_argument("n", type=int, nargs="?", default=1)
    p.set_defaults(fn=cmd_use)
    p = sub.add_parser("restock", help="add stock to an item")
    p.add_argument("id", type=int); p.add_argument("n", type=int)
    p.set_defaults(fn=cmd_restock)
    p = sub.add_parser("shop", help="print the shopping list")
    p.set_defaults(fn=cmd_shop)
    p = sub.add_parser("export", help="write items to a CSV file")
    p.add_argument("path"); p.set_defaults(fn=cmd_export)
    p = sub.add_parser("import", help="add items from a CSV file (the export format)")
    p.add_argument("path"); p.set_defaults(fn=cmd_import)
    p = sub.add_parser("wipe", help="delete everything")
    p.add_argument("--yes", action="store_true"); p.set_defaults(fn=cmd_wipe)
    p = sub.add_parser("serve", help="run the web app")
    p.add_argument("--port", type=int, default=8040); p.set_defaults(fn=cmd_serve)
    args = ap.parse_args(argv)
    return args.fn(args) or 0


if __name__ == "__main__":
    sys.exit(main())
