"""ledger-admin - maintenance commands for operators."""
import sys

from admin_tools import reindex, reset

COMMANDS = {"reset": reset.run, "reindex": reindex.run}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] not in COMMANDS:
        print("usage: ledger-admin reset | reindex")
        return 2
    return COMMANDS[argv[0]](argv[1:]) or 0


if __name__ == "__main__":
    sys.exit(main())
