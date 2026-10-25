I've added a feature map to `fixture/`, so the next agent can read it instead of exploring the CLI again. The full strict check (`check --strict --rerun`) exits 0: nothing stale, broken, unmapped or unproven.

**One thing is broken: `export` crashes on your real notes.** I didn't fix it because you asked for a map, not code changes. In `commands/export.py`, the CSV writer is only told about `id, title, body`, but every note also has `tags`, so it raises `ValueError: dict contains fields not in fieldnames: 'tags'`. Since every note has tags, any export fails. The fix is either `extrasaction="ignore"` or adding `tags` to `COLUMNS`. The map marks Export as `failing`, with the failed run recorded.

**What's in the repo now:**
- **`FEATURES.md`** lists six features: Add, List, Search, Tag, Export and Purge. Each one has a one-line description, its command, the path through the code from `notes.py` to `notes.json`, what it changes, and a status saying how I know it works. `debug-dump` is listed under "Not features" as a developer tool, so it doesn't count as missing.
- **`.features/`** holds a standalone copy of the checker plus a saved record of each test run. `python .features/features.py check --rerun` re-runs those commands and reports anything that has moved or stopped working, without the skill installed.
- **`AGENTS.md`** is new. It tells future agents to read `FEATURES.md` first, and that `notes.json` holds your real notes, so anything that writes must run against a copy.

**What was run against your data:**
- `list` and `search` only read, so they ran in the repo.
- `add`, `tag`, `purge --yes` and `export` ran in a throwaway copy of the repo.
- `notes.json` is byte-for-byte unchanged, and no `purge.log` or CSV file was created in the repo.

The repo isn't under git, so there's nothing to commit. If you put it in git later, commit `.features/` along with `FEATURES.md`.

<!-- file written by the agent: fixture/AGENTS.md -->
# AGENTS

Read FEATURES.md before driving or changing this app. `python .features/features.py check --rerun` says what moved or stopped working since it was proven.

`notes.json` holds the user's real notes: run anything that writes (add, tag, export, purge) with `prove --copy` or against a copy, never in place.


<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

What the system has and how each feature is reached. The commands that keep it true need
no skill installed; their `--help` says the rest, so the script never needs reading:
- `python .features/features.py check --rerun`: every entry point against the code, and every
  recorded run (.features/<feature>.json) run again, naming what moved or stopped working.
- `python .features/features.py prove --feature "<name>" [--copy] -- <command>`: run an entry
  point and record it (`--copy` runs it in a throwaway copy, for anything that writes data).
- status: `proven` (a passing run is recorded), `failing` (a failing run is recorded), `traced`
  (read start to end, not run) or `suspected`, then how you know.

All commands go through `HANDLERS` in notes.py and read/write `notes.json` via store.py
(the user's real notes: anything that writes must be proven with `--copy`).

## Add
- what: Add a note with a title, body and optional repeated `--tag`; prints its new id.
- cli: `add` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `PATH` @ store.py
- effect: appends a note to notes.json
- status: proven: `add Test "hello body" --tag x` in a copy printed `added #4`

## List
- what: List every note (id, title, tags), optionally only those with `--tag <name>`.
- cli: `list` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `PATH` @ store.py
- status: proven: `list` printed all 3 notes with tags

## Search
- what: Show notes whose title or body contains the query, case-insensitive.
- cli: `search` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `PATH` @ store.py
- status: proven: `search dune` found #3 Books

## Tag
- what: Add a tag to the note with the given id (no duplicate tags); exits 1 if no such note.
- cli: `tag` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/tag.py > `save` @ store.py > `PATH` @ store.py
- effect: rewrites notes.json
- status: proven: `tag 1 urgent` in a copy printed `tagged #1 urgent`

## Export
- what: Write all notes (id, title, body) to a CSV file at the given path, for spreadsheets.
- cli: `export` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/export.py > `writerow` @ commands/export.py
- effect: writes the CSV at `path`
- status: failing: `export out.csv` (in a copy) crashes with ValueError: notes carry a `tags` field not in `COLUMNS`, DictWriter raises

## Purge
- what: Delete ALL notes; refuses (exit 1) without `--yes`.
- cli: `purge` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `PATH` @ store.py
- effect: empties notes.json and appends a line to purge.log beside it
- status: proven: `purge --yes` in a copy printed `all notes deleted`

## Not features
- cli: `debug-dump` @ notes.py: developer dump of raw notes.json; no help text, not a user command
