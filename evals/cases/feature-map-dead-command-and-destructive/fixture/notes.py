"""notes: a tiny note-taking CLI.  python notes.py <command> ..."""
import argparse, sys

import store
from commands import add, export, listing, purge, search

HANDLERS = {
    "add": add.run,
    "list": listing.run,
    "search": search.run,
    "export": export.run,
    "purge": purge.run,
}


def parser():
    p = argparse.ArgumentParser(prog="notes")
    sub = p.add_subparsers(dest="command", required=True)
    a = sub.add_parser("add", help="add a note")
    a.add_argument("title")
    a.add_argument("body")
    a.add_argument("--tag", action="append", default=[])
    sub.add_parser("list", help="list notes").add_argument("--tag")
    sub.add_parser("search", help="full-text search").add_argument("query")
    sub.add_parser("export", help="write all notes to a JSON file").add_argument("path")
    sub.add_parser("purge", help="delete ALL notes").add_argument("--yes", action="store_true")
    sub.add_parser("sync", help="sync notes with the cloud")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    handler = HANDLERS.get(args.command)
    return handler(store.Store(), args)


if __name__ == "__main__":
    sys.exit(main())
