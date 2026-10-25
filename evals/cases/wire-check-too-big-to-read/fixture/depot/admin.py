"""depot-admin - operator tools."""
import sys

from depot.admin_tools import compact, reseed

TOOLS = {"compact": compact.run, "reseed": reseed.run}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] not in TOOLS:
        print("usage: depot-admin " + " | ".join(sorted(TOOLS)))
        return 2
    return TOOLS[argv[0]](argv[1:]) or 0


if __name__ == "__main__":
    sys.exit(main())
