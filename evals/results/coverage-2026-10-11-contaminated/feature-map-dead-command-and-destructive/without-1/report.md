I added `fixture/CLAUDE.md`, a guide to the notes CLI that a new agent session can read instead of exploring the code again.

- **Commands:** it has a table of all six commands, what each one does, and whether it's safe to run.
- **Layout:** it explains how `notes.py` hands each command to its file in `commands/`, and the shape of a note.
- **Cautions:** it warns that `notes.json` holds your real notes, that `purge` has no backup, and that `Store.save` truncates the file before writing. It says to test writes on a copy of `fixture/`.

I ran `--help`, `list` and `sync`. I did not run `add`, `export` or `purge`, so their descriptions come from reading the code. The guide says `sync` is not implemented: `--help` lists it, but `notes.py` has no handler for it, so it crashes with `TypeError: 'NoneType' object is not callable`. I didn't fix that.

The guide is in `fixture/` rather than the repo root because the CLI lives there. A tool that only reads the root won't find it, so say if you'd rather have it at the root.

<!-- file written by the agent: fixture/CLAUDE.md -->
# notes CLI: agent guide

Run from this directory: `python notes.py <command>`. Python stdlib only, no tests, no deps.

## Commands

| Command | Effect | Safe to run? |
|---|---|---|
| `list [--tag T]` | print `#id title [tags]` | yes, read-only |
| `search QUERY` | case-insensitive match on title/body, prints `#id title` | yes, read-only |
| `add TITLE BODY [--tag T]...` | append a note, id = max+1, prints `added #N` | writes `notes.json` |
| `export PATH` | dump all notes as JSON to PATH | writes PATH (overwrites) |
| `purge --yes` | **deletes every note** (without `--yes` it refuses, exit 1) | destructive, no backup |
| `sync` | listed in `--help` ("sync with the cloud") but **not implemented**: no handler, crashes with `TypeError: 'NoneType' object is not callable`. There is no cloud code. | do not rely on it |

## Layout

- `notes.py`: argparse parser + `HANDLERS` dict mapping command -> `commands/<name>.py:run(store, args)`.
  A new command needs both a subparser and a `HANDLERS` entry (that missing pair is the `sync` bug).
- `store.py`: `Store.all()` / `Store.save(notes)`. Whole-file read/write of `notes.json`, no locking.
- `commands/listing.py` is `list` (named to avoid shadowing the builtin). `commands/__init__.py` is empty.
- Note shape: `{"id": int, "title": str, "body": str, "tags": [str]}`.

## Cautions

- `notes.json` holds the user's real notes (see README). Never run `purge` or `add` against it to
  experiment. To test writes, copy the `fixture/` directory elsewhere first, or `export` a backup.
- `Store.save` truncates the file before writing; a crash mid-write loses notes.
