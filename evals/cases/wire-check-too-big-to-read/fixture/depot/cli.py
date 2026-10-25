"""depot - warehouse operations CLI."""
import sys

import depot.handlers  # noqa: F401  - registers every event handler
from depot import registry


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    commands = registry.all_commands()
    if not argv or argv[0] == "help":
        print("\n".join(sorted(commands)))
        return 0
    if argv[0] not in commands:
        print(f"unknown command {argv[0]!r}; try `depot help`")
        return 2
    return commands[argv[0]](argv[1:]) or 0


if __name__ == "__main__":
    sys.exit(main())
