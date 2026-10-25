I've updated `fixture/CLAUDE.md` to match what the CLI does now. I ran all 30 commands on a throwaway copy of the repo, and your real `notes.json` is unchanged (same checksum before and after). I only changed the docs, not the code.

**What changed**

1. **`search` was renamed to `find`.** `python notes.py search …` now fails with a usage error (exit 2). `find` works the same way the old `search` did, archived notes included. The code is still in `commands/search.py`.
2. **`due` is broken: it swaps the day and month.** It now reads the date as year-day-month. `due 1 2026-11-02` saves `2026-02-11`, and any date with a day above 12, like `2026-10-25`, crashes. Because the date is checked before the note lookup, a bad date crashes even when the note doesn't exist. The `--help` text still says `YYYY-MM-DD`, which is now wrong.
3. **`upcoming` is broken.** It crashes with a TypeError whenever any note has a due date, and two of your three notes do, so it fails on your data even with default options.

**Everything else still matches the docs:** list, show, find, tags, the archived/pinned/starred lists, count, stats, recent, oldest, longest, overdue, debug-dump, export/import, add/edit/rename/tag/untag, the toggle commands (still printing `pind`/`stard`), and purge. The known problems also still happen: the empty-store crashes in `stats`/`oldest`/`longest`, duplicate tags from `add`, and `import` creating duplicate notes.

**Other doc edits:** I added exit code 2 for usage errors, and noted that a crash also exits 1, so you can't tell a crash from "no note" by the exit code alone.

The `due` and `upcoming` problems look like real bugs in the new code rather than intended changes, so I documented them instead of fixing them. If you want, I can fix both (`due` needs its date format changed back to `%Y-%m-%d`, and `upcoming` needs to compare dates with dates). I can also add `search` back as a second name for `find`.