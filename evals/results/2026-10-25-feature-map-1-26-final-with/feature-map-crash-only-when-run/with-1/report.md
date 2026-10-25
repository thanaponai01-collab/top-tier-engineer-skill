I added `FEATURES.md` at the root of `fixture/`, plus a `.features/` folder that holds the run records and a copy of the checker. The next session can read the map instead of digging through the code, then run `python .features/features.py check --strict --rerun` to confirm it still matches. That check passes now with 0 stale, 0 unmapped and 0 unproven.

**What's in the map.** All commands are `python notes.py <command>`.
- **add, list, search, tag, purge:** each was run, and its output matched what the map says (for example, `search dune` printed `#3 Books`). Each entry gives what the command does, how it's called, the path through the code to where it reads or writes `notes.json`, and what it changes.
- **export:** this one is broken. `python notes.py export out.csv` crashes with `ValueError: dict contains fields not in fieldnames: 'tags'`, and leaves a CSV with only the header row. The cause is that `commands/export.py` sets up its CSV columns as `id, title, body`, but every note also has `tags`. The map marks export as read-but-not-working rather than proven. The failed run is kept, so the check will start flagging the record once the bug is fixed, and that's the point to re-run and update it. A one-line fix is `csv.DictWriter(..., extrasaction="ignore")`. Note that tags still wouldn't be exported after that fix. I haven't changed any code.
- **debug-dump:** listed under "Not features". It's a developer command that prints the raw `notes.json` and has no help text.

**Your notes are safe.** Every command that writes (add, tag, purge, export) ran in a throwaway copy of the repo. Afterwards I compared `notes.json` byte-for-byte with a backup taken before the runs, and it hadn't changed. The map also warns future sessions never to run `purge` against the real file.

`fixture/` isn't a git repository, so nothing was committed. If you put it under version control, commit `.features/` along with `FEATURES.md`.

<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

What the `notes` CLI can do and how each feature is reached. Every command is
`python notes.py <command> ...`, dispatched by `HANDLERS` in notes.py to `commands/<file>.py::run`.
All data lives in `notes.json` at the repo root (the owner's real notes): run anything that writes
with `prove --copy` or against a copy, never on the real file.
Keep it true: `python .features/features.py check --strict --rerun` tests every entry point against
the code and re-runs every recorded proof (.features/<feature>.json).

## Add
- what: Save a new note with a title, body and optional tags; prints its new id.
- cli: `add` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `PATH` @ store.py
- effect: appends a note `{id, title, body, tags}` to notes.json (id = max id + 1).
- status: proven: `add "Test" "body" --tag x` in a repo copy printed `added #4`

## List
- what: Show every note as `#id title [tags]`, optionally only those with one tag (`--tag NAME`).
- cli: `list` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `PATH` @ store.py
- status: proven: `list --tag home` printed notes #1 and #3

## Search
- what: Find notes whose title or body contains a text (case-insensitive); prints `#id title`.
- cli: `search` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `PATH` @ store.py
- status: proven: `search dune` printed `#3 Books`

## Tag
- what: Add a tag to an existing note by id (no-op if it already has it); exit 1 if no such id.
- cli: `tag` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/tag.py > `save` @ store.py > `PATH` @ store.py
- effect: rewrites notes.json with the tag appended to that note.
- status: proven: `tag 1 urgent` in a repo copy printed `tagged #1 urgent`

## Export
- what: Write all notes to a CSV file (columns id, title, body) for a spreadsheet.
- cli: `export` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/export.py > `DictWriter` @ commands/export.py
- effect: writes the CSV at the given path; tags are not exported.
- status: traced: BROKEN at runtime: `export out.csv` crashes with `ValueError: dict contains fields not in fieldnames: 'tags'` (DictWriter in commands/export.py has no `extrasaction="ignore"`); leaves a CSV with only the header row

## Purge
- what: Delete ALL notes (empties notes.json); refuses and exits 1 without `--yes`.
- cli: `purge` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `PATH` @ store.py
- effect: notes.json becomes `[]`. Destructive and irreversible: never run on the real repo.
- status: proven: `purge --yes` in a repo copy printed `all notes deleted`

## Not features
- cli: `debug-dump` @ notes.py: developer command, prints raw notes.json; no help text, not for users
