"""notes: a note-taking CLI.  python notes.py <command> ...  (python notes.py --help)"""
import argparse, sys

import store
from commands import add, archive, archived, count, debug_dump, due, edit, export, import_cmd, list_cmd, longest, oldest, overdue, pin, pinned, purge, recent, rename, search, show, star, starred, stats, tag, tags, unarchive, unpin, unstar, untag, upcoming

HANDLERS = {
    "add": add.run,
    "list": list_cmd.run,
    "show": show.run,
    "edit": edit.run,
    "search": search.run,
    "tag": tag.run,
    "untag": untag.run,
    "tags": tags.run,
    "rename": rename.run,
    "archive": archive.run,
    "unarchive": unarchive.run,
    "archived": archived.run,
    "pin": pin.run,
    "unpin": unpin.run,
    "pinned": pinned.run,
    "star": star.run,
    "unstar": unstar.run,
    "starred": starred.run,
    "count": count.run,
    "stats": stats.run,
    "recent": recent.run,
    "oldest": oldest.run,
    "longest": longest.run,
    "export": export.run,
    "import": import_cmd.run,
    "due": due.run,
    "overdue": overdue.run,
    "upcoming": upcoming.run,
    "purge": purge.run,
    "debug-dump": debug_dump.run,
}


def parser():
    p = argparse.ArgumentParser(prog="notes")
    sub = p.add_subparsers(dest="command", required=True)
    s_add = sub.add_parser("add", help='add a note')
    s_add.add_argument("title")
    s_add.add_argument("body")
    s_add.add_argument("--tag", action='append', default=[])
    s_list_cmd = sub.add_parser("list", help='list notes that are not archived')
    s_list_cmd.add_argument("--tag")
    s_show = sub.add_parser("show", help='print one note')
    s_show.add_argument("id", type=int)
    s_edit = sub.add_parser("edit", help="replace a note's body")
    s_edit.add_argument("id", type=int)
    s_edit.add_argument("body")
    s_search = sub.add_parser("search", help='full-text search')
    s_search.add_argument("query")
    s_tag = sub.add_parser("tag", help='add a tag to a note')
    s_tag.add_argument("id", type=int)
    s_tag.add_argument("name")
    s_untag = sub.add_parser("untag", help='remove a tag from a note')
    s_untag.add_argument("id", type=int)
    s_untag.add_argument("name")
    s_tags = sub.add_parser("tags", help='list every tag with its count')
    s_rename = sub.add_parser("rename", help="change a note's title")
    s_rename.add_argument("id", type=int)
    s_rename.add_argument("title")
    s_archive = sub.add_parser("archive", help='archive a note')
    s_archive.add_argument("id", type=int)
    s_unarchive = sub.add_parser("unarchive", help='restore an archived note')
    s_unarchive.add_argument("id", type=int)
    s_archived = sub.add_parser("archived", help='list archived notes')
    s_pin = sub.add_parser("pin", help='pin a note')
    s_pin.add_argument("id", type=int)
    s_unpin = sub.add_parser("unpin", help='unpin a note')
    s_unpin.add_argument("id", type=int)
    s_pinned = sub.add_parser("pinned", help='list pinned notes')
    s_star = sub.add_parser("star", help='star a note')
    s_star.add_argument("id", type=int)
    s_unstar = sub.add_parser("unstar", help='unstar a note')
    s_unstar.add_argument("id", type=int)
    s_starred = sub.add_parser("starred", help='list starred notes')
    s_count = sub.add_parser("count", help='how many notes')
    s_stats = sub.add_parser("stats", help='notes, archived share, tags per note')
    s_recent = sub.add_parser("recent", help='newest notes first')
    s_recent.add_argument("--limit", type=int, default=5)
    s_oldest = sub.add_parser("oldest", help='the oldest note')
    s_longest = sub.add_parser("longest", help='the note with the longest body')
    s_export = sub.add_parser("export", help='write all notes to a CSV file')
    s_export.add_argument("path")
    s_import_cmd = sub.add_parser("import", help='add notes from a CSV file made by export')
    s_import_cmd.add_argument("path")
    s_due = sub.add_parser("due", help="set a note's due date (YYYY-MM-DD)")
    s_due.add_argument("id", type=int)
    s_due.add_argument("date")
    s_overdue = sub.add_parser("overdue", help='notes whose due date has passed')
    s_overdue.add_argument("--today", default='2026-10-25')
    s_upcoming = sub.add_parser("upcoming", help='notes due in the next N days')
    s_upcoming.add_argument("--days", type=int, default=30)
    s_upcoming.add_argument("--today", default='2026-10-25')
    s_purge = sub.add_parser("purge", help='delete ALL notes')
    s_purge.add_argument("--yes", action='store_true')
    s_debug_dump = sub.add_parser("debug-dump")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    return HANDLERS[args.command](store, args)


if __name__ == "__main__":
    sys.exit(main())
