import sys

from inventory import reserve_stock


def main(argv):
    item, qty = argv[1], int(argv[2])
    print(reserve_stock(item, qty))


if __name__ == "__main__":
    main(sys.argv)
