I mapped the CLI into `fixture/FEATURES.md`. Along the way I found that **`export` is broken**: it crashes on every run. `python notes.py export out.csv` exits 1 with `ValueError: dict contains fields not in fieldnames: 'tags'`. In `commands/export.py`, `COLUMNS = ["id", "title", "body"]`, but every note also has a `tags` key, and `csv.DictWriter` refuses extra keys by default. So the CSV export the README describes doesn't work right now. I didn't change the code. The fix is either `extrasaction="ignore"` (export without tags) or adding `"tags"` to `COLUMNS`, depending on whether you want tags in the spreadsheet.

**What's in the repo for the next session:**
- **`FEATURES.md`** covers six commands: `add`, `list`, `search`, `tag`, `export` and `purge`. Each one has a one-line description, how to run it, the code path from `notes.py` to the line that reads or writes `notes.json`, what it changes, and how I know it works. `debug-dump` is listed separately as a developer tool, since it has no help text.
- **`.features/`** holds a saved record of each run, plus a copy of the checker. `python .features/features.py check --strict --rerun` reruns those commands and fails if a command was renamed or removed, or if something that worked has stopped working. It needs no plugin installed.
- **`CLAUDE.md`** is a short pointer that tells future agents to read `FEATURES.md` first, run the check, and never run `add`, `tag` or `purge` against the real `notes.json`.

**Status:** I ran `add`, `list`, `search`, `tag` and `purge`, and all five worked. `export` is marked as read but failing, and its failed run is kept on record. The check passes with nothing missing or out of date.

**Your notes are untouched.** Everything that writes (`add`, `tag`, `export`, `purge --yes`) ran in a throwaway copy of the repo. `notes.json` has the same hash before and after, and no `purge.log` or `out.csv` was left in the repo.

Nothing is committed: `fixture/` isn't a git repository yet. When you do commit, include `.features/` along with `FEATURES.md` and `CLAUDE.md`.

<!-- file written by the agent: fixture/CLAUDE.md -->
# Agent notes

Read `FEATURES.md` first: every command of this CLI, what it does, its code path and its status.
Before trusting it, run `python .features/features.py check --rerun`; after adding, renaming or
removing a command, update the map and run `check --strict --rerun`.
`notes.json` holds the owner's real notes: never run `add`, `tag` or `purge` against it.


<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

What the `notes` CLI does and how each feature is reached (`python notes.py <command>`).
Keep it true: `python .features/features.py check --rerun` tests every entry point against the code and
re-runs every recorded proof (.features/<feature>.json), failing on any that broke.
All commands read/write `notes.json` beside `store.py` (the owner's real notes): run anything that
writes with `prove --copy`, never against the repo itself.

## Add
- what: Save a new note with a title, body and optional tags; prints its id.
- cli: `add` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `PATH` @ store.py
- effect: appends a note to notes.json (id = max id + 1)
- status: proven: ran `add` in a throwaway copy, printed `added #4`

## List
- what: Show every note's id, title and tags, optionally only those with one tag (`--tag`).
- cli: `list` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `PATH` @ store.py
- status: proven: ran `list --tag home`, printed notes 1 and 3

## Search
- what: Find notes whose title or body contains a word (case-insensitive).
- cli: `search` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `PATH` @ store.py
- status: proven: ran `search dune`, printed `#3 Books`

## Tag
- what: Add a tag to an existing note by id (no-op if already tagged; exit 1 if no such note).
- cli: `tag` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/tag.py > `save` @ store.py > `PATH` @ store.py
- effect: rewrites notes.json with the tag added
- status: proven: ran `tag 1 urgent` in a throwaway copy, printed `tagged #1 urgent`

## Export
- what: Write all notes to a CSV (columns id, title, body) to open in a spreadsheet.
- cli: `export` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/export.py > `DictWriter` @ commands/export.py
- effect: writes the CSV at the given path
- status: traced: CRASHES when run: `DictWriter` raises ValueError on each note's `tags` key (not in `COLUMNS`); failed receipt kept

## Purge
- what: Delete ALL notes (refuses without `--yes`) and log the purge.
- cli: `purge` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `PATH` @ store.py
- effect: empties notes.json; appends `purged all notes` to purge.log beside it
- status: proven: ran `purge --yes` only in a throwaway copy, printed `all notes deleted`

## Not features
- cli: `debug-dump` @ notes.py: developer dump of raw notes.json; no help text, not a user command
