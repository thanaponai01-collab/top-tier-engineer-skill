import argparse

import store
from billing.refunds import refund
from money import fmt
from ops.backup import backup, restore
from reports.dashboard import render


def main(argv=None):
    ap = argparse.ArgumentParser(prog="shop")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p = sub.add_parser("show")
    p.add_argument("order_id")
    sub.add_parser("dashboard")
    p = sub.add_parser("refund")
    p.add_argument("order_id")
    p.add_argument("line_id")
    p = sub.add_parser("backup")
    p.add_argument("path")
    p = sub.add_parser("restore")
    p.add_argument("path")
    args = ap.parse_args(argv)

    orders = store.load_orders()
    if args.cmd == "list":
        for o in orders:
            print(f"{o.id}  {o.customer:<10} {o.status:<16} {fmt(o.total):>10}")
    elif args.cmd == "show":
        o = store.find(orders, args.order_id)
        print(f"{o.id} for {o.customer} ({o.status}), total {fmt(o.total)}")
        for line in o.lines:
            print(f"  {line.id:<6} {line.sku:<12} {line.qty} x {fmt(line.price_cents)}")
    elif args.cmd == "dashboard":
        print(render(orders))
    elif args.cmd == "refund":
        o = store.find(orders, args.order_id)
        print(f"{o.id} total before refund: {fmt(o.total)}")
        print(refund(o, args.line_id))
        store.save_orders(orders)
    elif args.cmd == "backup":
        print(backup(orders, args.path))
    elif args.cmd == "restore":
        restored = restore(args.path)
        store.save_orders(restored)
        print(f"Restored {len(restored)} orders from {args.path}")


if __name__ == "__main__":
    main()
