I added a guide to the CLI at `fixture/AGENTS.md`, plus a one-line `fixture/CLAUDE.md` that imports it. Claude Code reads `CLAUDE.md` when a session starts, and other agent tools look for `AGENTS.md`, so either kind of agent will find it.

The guide covers:
- **Data safety, first:** every command reads and writes the real `notes.json`, and there's no way to point the CLI at a different file. `add`, `tag` and `purge --yes` change your actual notes. It tells agents to test on a copy of the repo, and never to run `purge`.
- **Commands:** a table of all seven, with arguments, whether each one writes, and what it prints. That includes `debug-dump`, which exists but doesn't show up in `--help`.
- **Known issues and code layout:** how the files fit together and the shape of the data.

**`export` is broken.** When I tested it with a temporary output path, it crashed with `ValueError: dict contains fields not in fieldnames: 'tags'`. The cause is that `commands/export.py` only lists `id, title, body` as columns, but every note also has tags. The output file ends up with just a header row, so the spreadsheet export currently doesn't work at all. I didn't fix it, because you need to choose how tags appear in your spreadsheet: probably a `tags` column joined with `;`, or just leave them out. Tell me which and I'll make the change.

I only ran commands that don't change anything (`--help`, `list`, `search`, and `export` to a temp file), so `notes.json` is untouched.

<!-- file written by the agent: fixture/AGENTS.md -->
# Agent guide: `notes` CLI

Read this before you start, so you don't have to work out the CLI again. Checked 2026-10-25 against Python 3.13.
If you change a command, update this file too.

## ⚠️ Data safety: read this first
- `notes.json` holds the owner's **real notes**. Don't lose or corrupt them.
- Every command reads and writes `notes.json` next to `store.py` (the path is hardcoded in
  `store.PATH`). There is **no flag, env var or config to use a different file**. Running `add`, `tag`
  or `purge` changes the real data.
- Before testing anything that writes, copy the whole repo to a temp dir and run it there
  (`cp -r fixture "$TMP/notes-copy"`). Or back up `notes.json` first and restore it afterwards.
- `Store.save` rewrites the file in place, not atomically. A crash mid-write can truncate it.

## Run
```
python notes.py <command> [args]      # from the repo root; stdlib only, no install step
python notes.py --help                # debug-dump isn't listed in help, but it exists
```

## Commands
| Command | Args | Writes? | Behavior |
|---|---|---|---|
| `add` | `TITLE BODY [--tag T]...` | yes | Appends `{id, title, body, tags}`. id = max existing + 1. Prints `added #N`. |
| `list` | `[--tag T]` | no | Prints `#id title  [tag, tag]`, optionally filtered to one exact tag. |
| `search` | `QUERY` | no | Case-insensitive substring match on title and body (not tags). Prints `#id title`. |
| `tag` | `ID NAME` | yes | Adds a tag if it isn't already there. Exits 1 with `no note #ID` if the id is unknown. |
| `export` | `PATH` | writes PATH only | **BROKEN**, see below. |
| `purge` | `[--yes]` | yes, **deletes everything** | Without `--yes` it prints a refusal and exits 1. With `--yes` it saves `[]`. Never run it on the real data. |
| `debug-dump` | none | no | Prints the raw `notes.json` contents as indented JSON. This is the easiest way to inspect the data. |

There's no command to delete or edit a single note. To do that, edit `notes.json` directly (carefully).

## Known issues
- **`export` crashes on any non-empty store.** `commands/export.py` uses
  `COLUMNS = ["id", "title", "body"]`, but notes also have `tags`. `csv.DictWriter` then raises
  `ValueError: dict contains fields not in fieldnames: 'tags'`. The output file is left with just a
  header row. The owner uses this CSV in a spreadsheet, so a fix probably means adding a `tags` column
  (for example joined with `;`) rather than silently dropping tags. Ask before choosing.
- A missing `notes.json` crashes every command (`FileNotFoundError`). An empty store has to be `[]`.

## Layout
- `notes.py`: argparse setup plus the `HANDLERS` map from command name to `commands/<x>.run`.
- `store.py`: `Store.all()`, `Store.save(notes)`, `Store.next_id()`.
- `commands/*.py`: one `run(store, args) -> exit code` per command. `list` lives in `listing.py` and
  `debug-dump` in `debug.py`.
- Data shape: a JSON list of `{"id": int, "title": str, "body": str, "tags": [str]}`.
- There are no tests and no git history.


<!-- file written by the agent: fixture/CLAUDE.md -->
@AGENTS.md
