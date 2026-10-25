I mapped the CLI in `fixture/`, and the next agent will be pointed to the map. While mapping it I found that **`export` is broken**: `python notes.py export out.csv` crashes with `ValueError: dict contains fields not in fieldnames: 'tags'`. `commands/export.py` only lists `id, title, body` as columns, but every note also has `tags`, so no CSV gets written. I haven't changed the code. You can either add `tags` as a CSV column or have the export skip it. If you fix it, run `prove --again --feature Export` to record a new result.

**What I added in `fixture/`:**
- **`FEATURES.md`**: one section per command. Each says what it does, the exact command, the code path from `notes.py` through the handler and `store.py` to `notes.json`, what it changes, and its status with the evidence.
- **`.features/`**: a recorded run for each command, plus a copy of the checker so it works without the skill installed.
- **`AGENTS.md`**: tells the next agent to read `FEATURES.md` first and run `python .features/features.py check --rerun`. That re-checks the map against the code and re-runs the recorded commands.

**Status of each command:**

| Feature | Status | How I know |
|---|---|---|
| add | proven | `added #4` |
| list | proven | `--tag home` showed notes #1 and #3 |
| search | proven | `dune` found `#3 Books` |
| tag | proven | `tagged #1 urgent` |
| purge | proven | `all notes deleted` (refuses without `--yes`) |
| export | **failing** | crash above |

`debug-dump` is listed under "Not features": it's a developer dump of the raw notes with no help text. It is still checked against the code.

**Your notes weren't touched.** `list` and `search` only read, so I ran them on the real `notes.json`. `add`, `tag`, `export` and `purge` ran only in a throwaway copy of the folder. Afterwards your `notes.json` was byte-for-byte the same as before, and no `purge.log` or `out.csv` was left in the folder.

`check --strict --rerun` exits 0 with nothing stale, unmapped or unproven, and the run shows `export` still failing. `fixture/` isn't a git repository, so nothing was committed. Commit `.features/` along with `FEATURES.md` and `AGENTS.md` if you put it under version control.

<!-- file written by the agent: fixture/AGENTS.md -->
# Agents

Read FEATURES.md before driving or changing this app. `python .features/features.py check --rerun` says what moved or stopped working since it was proven.


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

## Add
- what: Save a new note with a title, a body and optional tags; prints its new id.
- cli: `add` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `PATH` @ store.py
- effect: appends a note to notes.json (id = max id + 1)
- status: proven: `add Test hello --tag x` in a throwaway copy printed `added #4`

## List
- what: Show every note's id, title and tags, optionally only those with one tag (`--tag`).
- cli: `list` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `PATH` @ store.py
- status: proven: `list --tag home` printed notes #1 and #3

## Search
- what: Find notes whose title or body contains a text, case-insensitively.
- cli: `search` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `PATH` @ store.py
- status: proven: `search dune` printed `#3 Books`

## Tag
- what: Add a tag to an existing note by id (exit 1 if no such note).
- cli: `tag` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/tag.py > `save` @ store.py > `PATH` @ store.py
- effect: rewrites notes.json with the tag added
- status: proven: `tag 1 urgent` in a throwaway copy printed `tagged #1 urgent`

## Export
- what: Write all notes (id, title, body) to a CSV file to open in a spreadsheet.
- cli: `export` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/export.py > `DictWriter` @ commands/export.py
- effect: writes the CSV at the given path
- status: failing: `export out.csv` crashes with ValueError, notes have a `tags` key not in COLUMNS (commands/export.py); no CSV is produced

## Purge
- what: Delete ALL notes (refuses without `--yes`) and append a line to purge.log.
- cli: `purge` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `PATH` @ store.py
- effect: empties notes.json; appends to purge.log beside it
- status: proven: `purge --yes` run only in a throwaway copy, printed `all notes deleted`

## Not features
- cli: `debug-dump` @ notes.py: developer dump of raw notes.json, no help text; not a user feature
