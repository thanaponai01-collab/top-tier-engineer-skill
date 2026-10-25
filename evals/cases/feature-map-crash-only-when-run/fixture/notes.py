"""notes: a small note-taking CLI.  python notes.py <command> ..."""
import argparse, sys

import store
from commands import add, debug, export, listing, purge, search, tag

HANDLERS = {
    "add": add.run,
    "list": listing.run,
    "search": search.run,
    "tag": tag.run,
    "export": export.run,
    "purge": purge.run,
    "debug-dump": debug.run,
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
    t = sub.add_parser("tag", help="add a tag to a note")
    t.add_argument("id", type=int)
    t.add_argument("name")
    sub.add_parser("export", help="write all notes to a CSV file for spreadsheets").add_argument("path")
    sub.add_parser("purge", help="delete ALL notes").add_argument("--yes", action="store_true")
    sub.add_parser("debug-dump")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    return HANDLERS[args.command](store.Store(), args)


if __name__ == "__main__":
    sys.exit(main())
