I updated `fixture/CLAUDE.md`, the agent guide, so it matches what the CLI does now. I checked every command by running it against a temporary copy of the repo. `notes.json` wasn't touched: its hash is the same before and after, and all three notes are still there. `AGENTS.md` and `README.md` only point to other places, so they didn't need changes.

**What changed in the CLI**

1. **`search` is now `find`.** The command was renamed but the code still lives in `commands/search.py`. Running `notes search …` now fails with `invalid choice` (exit 2). `find` works the same way the old `search` did.
2. **`due` swaps month and day.** The help still says `YYYY-MM-DD`, but the code reads the date as year-day-month. So `due 1 2026-11-02` quietly saves **2026-02-11** and reports success. Any date with a day over 12, like `2026-11-20`, crashes with a ValueError. For now the guide says to enter `YYYY-DD-MM` and check the date it prints back.
3. **`upcoming` is broken.** It crashes with `TypeError: '<=' not supported between ... 'datetime.date' and 'datetime.datetime'` whenever any note is due on or after `--today`. With your current notes, that's every run with the default date. `overdue` still works.

**Unchanged:** the guide's other claims all still hold:
- All other commands and their output formats.
- The misspelled messages (`pind`, `stard`, `unpind`, `unstard`).
- The hardcoded `2026-10-25` dates.
- The crashes on an empty store (`stats`, `oldest`, `longest`).
- Export and import still lose data, and importing your own export duplicates every note.
- `purge` still refuses without `--yes` and writes a line to `purge.log`.

In the guide I updated the command table, the list of commands that write to the file, the file-name mapping, and the known-problems section.

I only changed the documentation, not the bugs themselves. Fixing `due` would be a one-line change, back to `'%Y-%m-%d'`. Fixing `upcoming` would mean comparing against a date (`today + timedelta(days=args.days)`) instead of a datetime. I can make either fix if you want.