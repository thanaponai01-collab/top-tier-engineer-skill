I added `fixture/CLAUDE.md`, which Claude Code loads automatically at the start of a session. I wrote it from reading the source and didn't run any commands. That includes the `sync` crash below, which comes from reading the code.

It covers:
- **Commands:** a table of the five working commands (`add`, `list`, `search`, `export`, `purge`), what each does, and whether it changes `notes.json`.
- **`sync`:** it appears in `--help` but has no handler in `HANDLERS`, so it would crash, and there is no cloud code.
- **Layout and note shape:** where the argparse setup, the handler table, the store and the per-command modules live, and the fields in a note.
- **Safety:** `notes.json` holds your real notes, and `purge --yes` wipes them all. The store path is hardcoded with no override, so the file recommends trying `add` or `purge` on a copy of the directory. `list`, `search` and `--help` are safe to run in place.

I used `CLAUDE.md` rather than touching your `README.md`. If you use other agent tools, renaming it to `AGENTS.md` would suit them better.

<!-- file written by the agent: fixture/CLAUDE.md -->
# notes CLI: agent orientation

Tiny Python note-taking CLI (stdlib only). Run from the repo root: `python notes.py <command>`.
Data is in `notes.json`. **These are the user's real notes. Never run mutating commands against it.**

## Commands

| Command | Effect | Mutates `notes.json`? |
|---|---|---|
| `add TITLE BODY [--tag T]...` | Append a note; id = max id + 1; prints `added #N` | **yes** |
| `list [--tag T]` | Print `#id title  [tags]`, optionally filtered by exact tag | no |
| `search QUERY` | Case-insensitive substring match on title or body; prints `#id title` | no |
| `export PATH` | Write all notes as JSON to PATH (overwrites PATH) | no |
| `purge --yes` | Replace all notes with `[]`. Without `--yes` it refuses (exit 1) | **yes, destroys everything** |
| `sync` | Listed in `--help` but **not implemented**: no handler in `HANDLERS`, so it crashes (`None` is not callable). There is no cloud code | n/a |

## Layout

- `notes.py`: argparse setup plus the `HANDLERS` dict (command name -> `commands/<x>.py:run`). A new command needs both a subparser and a `HANDLERS` entry. `sync` has only the former.
- `store.py`: `Store.all()` / `Store.save(notes)`. Reads and writes `notes.json` next to the file (the path is hardcoded, with no env override). `save` rewrites the whole file non-atomically.
- `commands/*.py`: one module per command, each exposing `run(store, args) -> exit code`.
- Note shape: `{"id": int, "title": str, "body": str, "tags": [str]}`.

## Working safely

- To try mutating commands, work on a copy of the directory (for example copy `fixture/` to a temp dir and run there), since `store.PATH` is fixed relative to `store.py`.
- Read-only commands (`list`, `search`, `--help`) are safe to run in place.
- There are no tests and no dependencies.
