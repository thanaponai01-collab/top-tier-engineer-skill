I added `fixture/FEATURES.md`, a map of what the notes CLI can do. The next session can read it first instead of exploring the code. The map's checker passes with every count at 0. Running the commands also turned up a bug: **`export` crashes on every run.**

**In the map:** one section per command, saying what it does, how you call it, and the chain of code from the command to the data it changes.
- **Ran successfully:** `add`, `list`, `search` and `tag`. Run records are in `fixture/.features/`. If those files change later, the checker will flag the map as out of date.
- **Not run:** `purge` deletes every note, so I only read its code. I didn't run it.
- **Bug:** `export out.csv` fails with `ValueError: dict contains fields not in fieldnames: 'tags'`. The CSV columns are only `id, title, body`, but every note also has `tags`, and the CSV writer rejects the extra field. It leaves behind a CSV with only the header row. The map records this; I didn't change the code. The usual fix is to add `extrasaction="ignore"` in `commands/export.py`, or to add a `tags` column.
- **Not counted as a feature:** `debug-dump`, an undocumented developer command that prints the raw notes file.

**Your notes are untouched.** Every command reads and writes `notes.json`, which your README says holds your real notes. I ran `add` and `tag` against a copy of it; the map's intro explains how to do that. `notes.json` is byte-for-byte identical to before.

To check whether the map still matches the code after a change, run `python <feature-map skill>/scripts/features.py check --strict`.

<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

The `notes` CLI: `python notes.py <command>`, dispatched by `HANDLERS` in notes.py. Every command
reads and writes `notes.json` next to store.py (`store.PATH`), which holds the owner's real notes:
to run a writing command safely, point `store.PATH` at a copy, e.g.
`python -c "import sys,store; store.PATH=sys.argv[1]; import notes; sys.exit(notes.main(sys.argv[2:]))" /tmp/copy.json add T B`.
Check this map with `python <feature-map skill>/scripts/features.py check --strict`.

## Add
- what: Save a new note with a title, a body and optional tags; prints its new id.
- cli: `add` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `PATH` @ store.py
- effect: appends a note `{id, title, body, tags}` to notes.json; id is max id + 1.
- status: proven: `add Test body --tag x` against a copy of notes.json printed `added #4`

## List
- what: Print every note as `#id title [tags]`, optionally only those with a given tag.
- cli: `list` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `PATH` @ store.py
- status: proven: `list --tag home` ran, exit 0

## Search
- what: Print notes whose title or body contains a text, case-insensitively.
- cli: `search` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `PATH` @ store.py
- status: proven: `search dune` ran, exit 0

## Tag
- what: Add a tag to an existing note by id (no-op if already tagged; exit 1 if no such note).
- cli: `tag` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/tag.py > `save` @ store.py > `PATH` @ store.py
- effect: rewrites notes.json with the tag appended.
- status: proven: `tag 1 urgent` against a copy of notes.json, exit 0

## Export
- what: Write all notes to a CSV (columns id, title, body) for opening in a spreadsheet.
- cli: `export` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/export.py > `DictWriter` @ commands/export.py
- effect: writes the CSV at the given path; reads notes.json only.
- status: traced: BROKEN in practice. `export out.csv` crashes with `ValueError: dict contains fields not in fieldnames: 'tags'` (COLUMNS lacks `tags` and no `extrasaction="ignore"`), leaving a header-only CSV. Failed receipt in .features/export.json.

## Purge
- what: Delete ALL notes; refuses unless `--yes` is given.
- cli: `purge` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `PATH` @ store.py
- effect: overwrites notes.json with `[]`. Destructive: never run against the real notes.json.
- status: traced: read end to end; not run because it deletes data.

## Not features
- cli: `debug-dump` @ notes.py: developer command, no help text; prints notes.json raw as JSON
