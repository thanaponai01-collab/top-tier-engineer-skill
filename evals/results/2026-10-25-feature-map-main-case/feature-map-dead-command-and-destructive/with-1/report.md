I added a feature map to `fixture/`, so the next session can read what the CLI does instead of rediscovering it. `features.py check --strict` exits 0 with every count at zero, and `notes.json` is byte-for-byte unchanged.

**What I left in the repo**
- **`FEATURES.md`**: one section per command. Each says what it does, how to call it, the path through the code to where it reads or writes (`notes.py` → `commands/<x>.py` → `store.py`), its check, and how I know it works.
- **`VERIFY.md` + `tests/test_notes.py`**: a check for each command. The tests run against a temporary copy of the notes, never your real `notes.json`. I planted a wrong result in each command and its check failed every time, so the checks really do catch breakage.
- **`.features/`, `.verify-state*`**: run records the tools use to notice when the code changes and the map goes out of date.
- **`README.md`**: two lines pointing to the map and the checks.

**Commands**

| Command | Status |
|---|---|
| `list`, `search`, `export` | Run for real. `export` wrote to a temp file outside the repo. |
| `add` | Run against a copy of the repo, so your real notes weren't changed. |
| `purge` | Only covered by the test on a temporary copy. I didn't run it on the CLI because it deletes all notes. |

**What I found:**
- **`sync` is broken.** It's listed in `--help` ("sync notes with the cloud") but nothing handles it, so `python notes.py sync` crashes with `TypeError: 'NoneType' object is not callable`. The map lists it under "Not features" and "Not built". If you implement it or remove it, the check will show the map needs updating.
- **`purge` is easy to misfire.** One `purge --yes` wipes the real notes, and only the `--yes` flag stands in the way. The map warns about it.

Before starting I backed up your notes to `../backup/notes.json.orig`, outside `fixture/`. You can delete it.

To keep the map honest, rerun `features.py check` after adding or renaming any command.

<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

`notes`: a note-taking CLI, run as `python notes.py <command>`. `notes.py` maps each subcommand to
`commands/<x>.py::run` through `HANDLERS`. Every command reads or writes `notes.json` beside
`store.py`. That file holds the owner's real notes, so run anything that writes against a copy
of the repo. The tests in `tests/test_notes.py` point `store.PATH` at a temp file.
Check this map: `python <feature-map>/scripts/features.py check --strict`. Run the checks with `python -m pytest -q tests`.

## Add
- what: Save a new note with a title, body and optional repeated `--tag`. Prints `added #<id>`.
- cli: `add` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `PATH` @ store.py
- effect: appends a note to notes.json with id = max id + 1
- verify: Add
- status: proven: ran `add` on a copy of the repo, it printed `added #4`

## List
- what: Print every note as `#id title  [tags]`, or only notes with `--tag <tag>`.
- cli: `list` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `PATH` @ store.py
- verify: List
- status: proven: ran `list`, it printed the 3 notes

## Search
- what: Print notes whose title or body contains the query, ignoring case.
- cli: `search` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `PATH` @ store.py
- verify: Search
- status: proven: ran `search dune`, it printed `#3 Books`

## Export
- what: Write all notes to the JSON file at the given path.
- cli: `export` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/export.py > `all` @ store.py > `PATH` @ store.py
- effect: creates or overwrites the file at the given path
- verify: Export
- status: proven: exported to a temp file outside the repo

## Purge
- what: Delete every note. Refuses and exits 1 without `--yes`.
- cli: `purge` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `PATH` @ store.py
- effect: overwrites notes.json with `[]`
- verify: Purge
- status: traced: not run on the CLI because it deletes the real notes; test_purge drives it on a temp store

## Not features
- cli: `sync` @ notes.py: in the parser ("sync notes with the cloud") but missing from HANDLERS; running it crashes with TypeError: 'NoneType' object is not callable

## Not built
- Cloud sync: only the `sync` parser stub exists.


<!-- file written by the agent: fixture/VERIFY.md -->
require: challenge

## Add
- path: notes.py, store.py, commands/add.py
- test: `python -m pytest -q tests/test_notes.py -k test_add`
- oracle: tests/test_notes.py
- fail-signal: add did not save the new note
- fail-proof: challenge dropped the new note from store.save in commands/add.py; test_add went red, restored

## List
- path: notes.py, store.py, commands/listing.py
- test: `python -m pytest -q tests/test_notes.py -k test_list`
- oracle: tests/test_notes.py
- fail-signal: list did not print every note
- fail-proof: challenge inverted the tag filter in commands/listing.py; test_list went red, restored

## Search
- path: notes.py, store.py, commands/search.py
- test: `python -m pytest -q tests/test_notes.py -k test_search`
- oracle: tests/test_notes.py
- fail-signal: search missed a body match
- fail-proof: challenge removed the body match in commands/search.py; test_search went red, restored

## Export
- path: notes.py, store.py, commands/export.py
- test: `python -m pytest -q tests/test_notes.py -k test_export`
- oracle: tests/test_notes.py
- fail-signal: export file does not match the notes
- fail-proof: challenge exported only the first note in commands/export.py; test_export went red, restored

## Purge
- path: notes.py, store.py, commands/purge.py
- test: `python -m pytest -q tests/test_notes.py -k test_purge`
- oracle: tests/test_notes.py
- fail-signal: purge --yes left notes behind
- fail-proof: challenge kept one note on purge in commands/purge.py; test_purge went red, restored

## Blind spots
- `sync` is declared in notes.py but has no handler; it crashes, so there is nothing to check
