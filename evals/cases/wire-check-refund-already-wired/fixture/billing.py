"""billing - charge and refund customers."""
import sys

from billing_cli import registry


def main(argv):
    commands = registry.all_commands()
    if not argv or argv[0] not in commands:
        print("usage: billing.py " + " | ".join(sorted(commands)))
        return 2
    return commands[argv[0]](argv[1:]) or 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
