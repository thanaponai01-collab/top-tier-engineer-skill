"""Usage: python cli.py export OUT_PATH"""
import sys

from invoices import export, load_invoices


def main(argv):
    if len(argv) < 2 or argv[0] != "export":
        print(__doc__.strip())
        return 2
    n = export(load_invoices(), argv[1])
    print(f"exported {n} invoices to {argv[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
