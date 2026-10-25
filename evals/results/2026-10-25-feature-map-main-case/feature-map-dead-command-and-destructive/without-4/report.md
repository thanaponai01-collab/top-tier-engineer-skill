I added `fixture/CLAUDE.md`, which Claude Code loads automatically at the start of every session. I also added a line to `README.md` pointing other agents to it.

**What's in it:**
- **A warning about your real notes:** the CLI always reads and writes `notes.json` next to the code, and there's no option to point it at another file. So agents shouldn't try `add` or `purge --yes` in the repo. The file explains how to test those commands on a temporary copy instead.
- **A table of every command:** its arguments, what it prints, and whether it changes `notes.json`. It also lists which commands are safe to run in place.
- **Quirks to know about:**
  - `sync` shows up in `--help` but isn't implemented. Running it crashes with `TypeError: 'NoneType' object is not callable`.
  - `search` matches titles and note text, but not tags.
  - `list --tag` takes only one tag.
  - `export` overwrites the target file without asking.
  - `purge --yes` deletes everything and keeps no backup.
  - On Windows, titles with accented or other non-English characters can come out garbled.
- **The data format and code layout:** including how to add a new command, which has to be registered in two places in `notes.py`.

**How I checked it:** I ran `--help`, `list`, `search`, `sync`, and `purge` without `--yes` in the repo; none of these change your notes. I ran `add` and `export` only on a temporary copy, which I then deleted. `notes.json` was never written to. I also deleted the `__pycache__` folders those runs created.

I didn't fix the `sync` crash or the other quirks, only documented them. I can fix them if you want.

<!-- file written by the agent: fixture/CLAUDE.md -->
# notes CLI: notes for agents

Read this before running anything. It is the result of reading every source file and running
each command. If you change the CLI, update this file too.

## ⚠️ `notes.json` holds the user's real notes

- `store.py` hardcodes `notes.json` next to the code. You can't point it at another file with a
  flag or an env var.
- **Never run `add` or `purge --yes` against this checkout just to try them out.** To exercise
  write paths, copy the repo to a temp dir and run there:
  `T=$(mktemp -d); cp -r . "$T"; cd "$T"; python notes.py add ...`
- Running the CLI creates `__pycache__/` dirs. Delete them afterwards.

## Commands (`python notes.py <cmd>`)

| Command | Args | Effect | Writes notes.json? |
|---|---|---|---|
| `list` | `[--tag TAG]` (one tag only) | Prints `#id title  [tags]` | no |
| `search` | `QUERY` | Case-insensitive substring match on title and body only (**not tags**). Prints `#id title` | no |
| `add` | `TITLE BODY [--tag T]...` (repeat `--tag` for more than one) | Appends a note with id = max+1. Prints `added #N` | **yes** |
| `export` | `PATH` | Dumps all notes as JSON to PATH. **Silently overwrites** PATH | no (but writes PATH) |
| `purge` | `--yes` | Without `--yes`: prints a refusal and exits 1. With it: **deletes every note**, no backup | **yes, destructive** |
| `sync` | none | **Not implemented.** It appears in `--help` but has no handler, so it crashes with `TypeError: 'NoneType' object is not callable`, exit 1 | no |

You can safely run `list`, `search`, `export <path outside repo>`, `sync`, `purge` (without
`--yes`) and `--help` in place.

## Data format

`notes.json` is a JSON array of `{"id": int, "title": str, "body": str, "tags": [str]}`.
The whole file is rewritten on every save, with no locking and no atomic write.

## Layout

- `notes.py`: argparse definitions plus the `HANDLERS` dict that maps commands to `commands/*.run`.
  Adding a subcommand means adding it in both places. A subparser without a handler crashes,
  which is what happens with `sync`.
- `store.py`: `Store.all()` / `Store.save(notes)`. Files are opened without `encoding=`, so on
  Windows they use the locale codepage, and non-ASCII titles can come out garbled.
- `commands/<name>.py`: each one has a `run(store, args) -> exit code`. `list` lives in `listing.py`.

There are no tests, no dependencies (stdlib only), and no git repo.
