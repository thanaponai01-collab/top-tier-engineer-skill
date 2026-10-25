"""shop - tiny stock-keeping CLI."""
import sys

import app.handlers  # noqa: F401  - registers every handler with the bus
from app import inventory


def cmd_stock(args):
    for sku, qty in sorted(inventory.load().items()):
        print(f"{sku:10} {qty:>5}")


def cmd_sell(args):
    sku, n = args[0], int(args[1])
    left = inventory.change(sku, -n)
    print(f"sold {n} {sku}, {left} left")


def cmd_restock(args):
    sku, n = args[0], int(args[1])
    now = inventory.change(sku, n)
    print(f"restocked {n} {sku}, {now} on hand")


COMMANDS = {"stock": cmd_stock, "sell": cmd_sell, "restock": cmd_restock}


def main(argv):
    if not argv or argv[0] not in COMMANDS:
        print("usage: shop.py stock | sell <sku> <n> | restock <sku> <n>")
        return 2
    COMMANDS[argv[0]](argv[1:])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
