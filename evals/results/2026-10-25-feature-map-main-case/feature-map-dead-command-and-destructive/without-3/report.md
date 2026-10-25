I added `fixture/CLAUDE.md`. Claude Code loads that file automatically at the start of each session. It covers:

- **The repo layout**, the shape of a note, and how commands are wired up: a subcommand needs both a subparser and an entry in `HANDLERS`.
- **A table of every command**: what arguments it takes, what it prints, and whether it writes to your notes.
- **Gotchas**, which I confirmed by running every command on a throwaway copy, never on your real `notes.json`:
  - **`python notes.py export notes.json` deletes all your notes.** The export empties the target file before it reads the notes. When the target is `notes.json`, the read then fails and the file is left empty.
  - **`sync` doesn't work.** It shows up in `--help`, but nothing runs it, so it always crashes.
  - `purge --yes` can't be undone. Nothing lets the tool use a different notes file, so the guide tells future sessions to experiment on a temp copy.

I documented these bugs but didn't fix them. The export one is a two-line fix: read the notes first, then open the output file. I can make that change and either implement `sync` or remove it if you'd like.

<!-- file written by the agent: fixture/CLAUDE.md -->
# notes CLI: agent guide

You don't need to rediscover this. Everything below was checked against the code and by running each
command on a scratch copy.

**`notes.json` holds the user's real notes.** Any command that writes (`add`, `purge --yes`, `export`)
changes or can destroy them. To try something out, copy the repo to a temp dir and run it there.
`store.py` always uses the `notes.json` next to itself, and there's no flag or env var to point it somewhere else.

## Layout
- `notes.py`: argparse setup plus the `HANDLERS` dict that maps each subcommand to `commands/<x>.run(store, args)`
- `store.py`: `Store.all()` / `Store.save(notes)` read and rewrite the whole of `notes.json`
- `commands/`: one module per subcommand (`list` lives in `listing.py`)
- Note shape: `{"id": int, "title": str, "body": str, "tags": [str]}`
- Standard library only. No dependencies, no tests.

## Commands (`python notes.py <cmd>`)
| Command | Effect | Writes? |
|---|---|---|
| `add TITLE BODY [--tag T]...` | appends a note with id = max+1, prints `added #N` | yes |
| `list [--tag T]` | prints `#id title  [tags]`, optionally filtered to one tag | no |
| `search QUERY` | case-insensitive substring match on title/body, prints `#id title` | no |
| `export PATH` | writes every note to PATH as JSON, overwriting it | yes (PATH) |
| `purge --yes` | deletes ALL notes. Without `--yes` it prints a refusal and exits 1 | yes |
| `sync` | **not implemented.** It's listed in `--help` but has no handler, so it crashes with `TypeError: 'NoneType' object is not callable` | no |

## Gotchas
- **`export notes.json` wipes all notes.** `export.py` opens the target for writing, which truncates
  it, *before* it reads the store. The read then fails with JSONDecodeError and `notes.json` is left
  at 0 bytes. Never export to the store path.
- `purge --yes` has no undo. Back up `notes.json` first.
- Writes aren't atomic. A crash partway through `save` can corrupt `notes.json`.
- Adding a command means adding a subparser in `parser()` **and** an entry in `HANDLERS`. Missing the
  second step is exactly what's wrong with `sync`.
