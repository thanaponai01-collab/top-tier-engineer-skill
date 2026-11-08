import sys
import time

from . import notify, store
from .jobs import expire_unpaid


def main(argv):
    cmd = argv[0] if argv else "list"
    orders = store.load()
    if cmd == "list":
        for o in orders:
            print(f"{o.id}\t{o.customer}\t{o.pages}p\t{notify.LABELS.get(o.status, o.status)}")
    elif cmd == "nightly":
        expired = expire_unpaid(orders, time.time())
        store.save(orders)
        print(f"expired {len(expired)} unpaid orders")
    else:
        print(f"unknown command {cmd}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
