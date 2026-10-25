"""ledger - order ledger CLI."""
import importlib
import sys

import settings
from commands import add, checkout, export, listing

COMMANDS = {"add": add.run, "list": listing.run, "checkout": checkout.run, "export": export.run}


def load_plugins():
    for name in settings.PLUGINS:
        importlib.import_module(f"integrations.{name}").install(COMMANDS)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    load_plugins()
    if not argv or argv[0] not in COMMANDS:
        print("usage: ledger " + " | ".join(sorted(COMMANDS)))
        return 2
    return COMMANDS[argv[0]](argv[1:]) or 0


if __name__ == "__main__":
    sys.exit(main())
