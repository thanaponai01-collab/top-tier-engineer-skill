import sys

from shop.checkout import checkout


def main(argv):
    order_id, email, region = argv[1], argv[2], argv[3]
    items = [(sku, int(qty)) for sku, qty in (pair.split("=") for pair in argv[4:])]
    out = checkout(order_id, items, email, region, member="--member" in argv)
    print(out if out else "payment failed")


if __name__ == "__main__":
    main(sys.argv)
