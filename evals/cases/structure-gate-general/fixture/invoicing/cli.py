"""invoicing price ORDER CUSTOMER | invoicing export FORMAT PATH"""
import argparse
import datetime

from invoicing import export_csv, export_json, models, pricing


def main(argv=None):
    ap = argparse.ArgumentParser(prog="invoicing")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("price")
    p.add_argument("order")
    p.add_argument("customer")
    e = sub.add_parser("export")
    e.add_argument("format", choices=["csv", "json"])
    e.add_argument("path")
    a = ap.parse_args(argv)
    if a.cmd == "price":
        order, customer = models.load_order(a.order), models.load_customer(a.customer)
        print(pricing.compute_price(order, customer, datetime.date.today()))
    else:
        invoices = list(models.store._read().get("invoices", {}).values())
        (export_csv if a.format == "csv" else export_json).write(invoices, a.path)


if __name__ == "__main__":
    main()
