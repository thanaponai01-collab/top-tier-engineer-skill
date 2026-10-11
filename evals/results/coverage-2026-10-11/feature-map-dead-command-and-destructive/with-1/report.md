I've written the feature map and ran the checker on it. It reports no stale or broken entries. `sync` shows up as unmapped on purpose, and there is no VERIFY.md yet. I have nothing more to change.

I wrote `fixture/FEATURES.md` for the next session. It covers five of the six CLI subcommands in `notes.py`. Each has a one-line description, its entry point, and the path from handler to the code that changes `notes.json`.

- **Proven by running:** `list`, `search` and `export`. I exported to a temp file, not into the repo.
- **Traced only:** `add` and `purge`. Both rewrite your real `notes.json`, so I did not run them. For `purge` I only ran the refusal path without `--yes`, which exits with code 1.
- **`sync` is dead:** it appears in `--help` but has no handler. Running it crashes with `TypeError: 'NoneType' object is not callable`. I recorded it under "Not built" instead of as a feature.
- **No VERIFY.md:** no feature links to a check, so each shows as unlinked. That is a gap I noted in the file, not something I filled.
- **No commit pins:** the repo isn't under git, so the statuses carry a date and no commit hash. The checker's drift alarm won't work until it is.

<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

Notes CLI (`python notes.py <command>`). Data: `notes.json` (the user's real notes; never run `add`/`purge` against it to test).
Dispatch: `HANDLERS` in notes.py maps subcommand to `commands/<name>.py:run(store, args)`; `store.py` reads/writes notes.json.
Check the map: `python <feature-map skill>/scripts/features.py check`.

## Add
- what: Add a note with a title, body and optional repeated `--tag`.
- cli: `add` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/add.py > `save` @ store.py
- effect: rewrites notes.json with the new note (next id = max+1)
- status: traced: read the chain; not run, it mutates the real notes

## List
- what: Print all notes, optionally only those with `--tag`.
- cli: `list` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/listing.py > `all` @ store.py
- status: proven: ran `list` and `list --tag work` (2026-10-11)

## Search
- what: Case-insensitive substring search over title and body.
- cli: `search` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/search.py > `all` @ store.py
- status: proven: ran `search dune`, found #3 (2026-10-11)

## Export
- what: Write all notes to a JSON file at the given path.
- cli: `export` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/export.py > `all` @ store.py
- effect: creates/overwrites the file at `path`
- status: proven: exported to a temp path, output is the notes JSON (2026-10-11)

## Purge
- what: Delete ALL notes; refuses without `--yes`.
- cli: `purge` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/purge.py > `save` @ store.py
- effect: notes.json becomes `[]` (destructive, no backup)
- status: traced: only the refusal path (no `--yes`, rc=1) was run; deletion path not run on purpose

## Not built
- `sync` is in `--help` (notes.py) but has no `HANDLERS` entry and no commands/sync.py: running it crashes with
  `TypeError: 'NoneType' object is not callable`. Dead entry point; a `wire-check` finding, not a feature.
- No VERIFY.md exists, so no feature has a `verify:` link (gap).
