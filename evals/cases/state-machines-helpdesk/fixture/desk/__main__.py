import sys
import time

from . import automations, export
from .sla import report
from .store import TicketStore

DATA = "data/tickets.json"


def main(argv):
    cmd = argv[0] if argv else "report"
    store = TicketStore.load(DATA)
    now = time.time()
    if cmd == "report":
        print(report.render(store.all(), now))
    elif cmd == "hourly":
        print(automations.run(store.all(), now))
        store.save(DATA)
    elif cmd == "export":
        sys.stdout.write(export.to_csv(store.all()))
    else:
        print(f"unknown command {cmd}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
