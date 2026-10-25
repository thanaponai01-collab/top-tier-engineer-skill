I added `fixture/CLAUDE.md`, which Claude Code loads automatically at the start of every session. It covers:

- **Each command:** its arguments, the exact output format, the exit codes, and whether it writes to disk. It includes `debug-dump`, which doesn't show up in `--help`.
- **A warning that `notes.json` holds your real notes.** It's always read from next to `store.py`, wherever the command is run from. The file includes a one-line way to try commands that write (`add`, `tag`, `purge`) on a temporary copy. Every behaviour I documented came from running the CLI on a copy, so your real notes weren't touched.
- **What it can't do:** search ignores tags, and there's no command to edit or delete a single note.
- **The note data format.**

**`export` is broken.** It crashes on every run with `ValueError: dict contains fields not in fieldnames: 'tags'`, and leaves behind a CSV with only the header row. This happens because `commands/export.py` lists only `id, title, body` as columns, but every note also has tags. I didn't fix it, because the right fix depends on whether you want tags in the spreadsheet. It's written up in the file's "Known issues" section. Tell me which you'd prefer and I'll fix it.

If you also use agents other than Claude Code, I can copy or symlink the file to `AGENTS.md`.

<!-- file written by the agent: fixture/CLAUDE.md -->
# notes CLI — agent guide

Python 3 stdlib only, no dependencies, no tests, not a git repo. Entry point: `python notes.py <command>`.
Last verified against Python 3.13 on 2026-10-25. If you change a command, update this file.

## ⚠ `notes.json` holds the user's real notes
Every command reads and writes `notes.json` next to `store.py` (the path is fixed in `store.PATH`;
your cwd doesn't change it). `add`, `tag` and `purge` overwrite it in place, and the write isn't
atomic. **To try out a command that writes, run it on a copy:**

```sh
T=$(mktemp -d); cp -r . "$T"; cd "$T"; python notes.py add "t" "b"
```

Never run `purge --yes` against the real repo.

## Commands (wiring is in `notes.py`, handlers are in `commands/`)

| Command | Args | Writes? | Behaviour / output | Exit |
|---|---|---|---|---|
| `add TITLE BODY` | `--tag NAME` (can repeat) | notes.json | `added #<id>`. id = max existing + 1 | 0 |
| `list` | `--tag NAME` | — | `#<id> <title>  [tag, tag]` one per line, filters by exact tag | 0 |
| `search QUERY` | | — | `#<id> <title>`. Case-insensitive substring match on title and body only (**tags are not searched**) | 0 |
| `tag ID NAME` | | notes.json | Adds the tag if it's missing. `tagged #<id> <name>` | 0, or 1 + `no note #<id>` |
| `export PATH` | | PATH | **Broken, see below** | — |
| `purge` | `--yes` | notes.json, purge.log | Without `--yes`: prints `refusing without --yes` and exits 1. With it: wipes every note and appends to `purge.log` next to notes.json | 0/1 |
| `debug-dump` | | — | Prints the whole notes.json pretty-printed. Not shown in `--help` | 0 |

The CLI has no command to edit or delete a single note. To do that, edit `notes.json` directly (on a copy first).

## Data shape
`notes.json` is a JSON list of `{"id": int, "title": str, "body": str, "tags": [str]}`.

## Known issues
- **`export` always crashes**: `commands/export.py` has `COLUMNS = ["id", "title", "body"]`, but
  every note also has a `tags` key, so `csv.DictWriter` raises
  `ValueError: dict contains fields not in fieldnames: 'tags'`. By then it has already written a
  header-only CSV to PATH. The fix depends on whether the user wants tags in the spreadsheet:
  either add a `tags` column (joined) or pass `extrasaction="ignore"`. Ask the user before choosing.
