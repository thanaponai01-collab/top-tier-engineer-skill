I've mapped all 7 commands in `fixture/`, and `features.py check --strict` passes with every count at 0. Your `notes.json` is unchanged: I compared it byte-for-byte against a backup after every run.

**What I left for the next session**
- **`FEATURES.md`**: one section per command, each with what it does, how to run it, and the code path (e.g. `main` @ notes.py > `run` @ commands/add.py > `save` @ store.py). Each also says how sure we are it works. `debug-dump` is listed under "Not features" as a developer-only tool.
- **`CLAUDE.md`**: a short pointer that agents read on startup. It says to read FEATURES.md first, never to run `add`, `tag` or `purge` against the real notes, and how to run the tests.
- **`tests/sandbox.py`**: runs the real CLI against a temp copy of notes.json, so commands that write are safe to try.
- **`tests/test_cli.py`** and **`VERIFY.md`**: one test per feature, all running on a copy of the notes.
- **`.features/`**: the saved results of each command I ran.

**Bug: `export` doesn't work.** It crashes with `ValueError: dict contains fields not in fieldnames: 'tags'` on every note, because `COLUMNS` in `commands/export.py:3` leaves out `tags`. The CSV you get has only its header row. Its test fails, and I left it failing rather than change your code or weaken the test. There are two ways to fix it: add a `tags` column, or pass `extrasaction="ignore"` so tags are left out of the CSV. Which one depends on what you want in your spreadsheet.

**Confidence labels:**
- **Add, List, Search, Tag**: I ran each one; Add and Tag ran on a copy of the notes. Their tests pass. They're labelled "traced" rather than "proven": "proven" also needs a step that breaks the code on purpose to show each test would catch it. That step only runs once every test passes, so it's blocked until export is fixed.
- **Purge**: I read the code path but didn't run it myself, because it deletes. Its test only ever deletes a temp copy.
- **Export**: I ran it and saved the failed result.

**Next step:** once export is fixed, run `verify.py advance .` until it says `done`, then change the four labels to `proven`. The folder isn't a git repo. If you make it one, add `.verify-state*`, `.pytest_cache` and `__pycache__` to `.gitignore`.

<!-- file written by the agent: fixture/CLAUDE.md -->
# notes CLI: read before working here

- **FEATURES.md** lists every command, what it does, its code path, and how sure we are it works. Read it before you go searching the code.
- **notes.json holds the owner's real notes.** Never run `add`, `tag` or `purge` against it.
  Use `python tests/sandbox.py <cmd> ...` (the real CLI, run on a temp copy).
- Tests: `python -m pytest tests -q` (sandboxed). VERIFY.md maps each feature to its test.
- Known bug: `export` crashes (`COLUMNS` in commands/export.py lacks `tags`); its test is red on purpose.
- After adding, renaming or removing a command, run feature-map's `features.py check --strict`.


<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

What `notes` can do and how each feature is reached. Run commands as `python notes.py <cmd>`.
notes.json holds the owner's real notes: drive anything that writes through
`python tests/sandbox.py <cmd> ...` (same CLI, temp copy of notes.json).
`python <feature-map>/scripts/features.py check --strict` tests this file against the code.

## Add
- what: Save a new note with a title, body and optional tags; prints its new id.
- cli: `add` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `notes.json` @ store.py
- effect: appends a note to notes.json (id = max id + 1)
- verify: Add
- status: traced: ran it (receipt in .features/); not `proven` until Export is fixed, since verify-loop's mutation proof needs the whole suite green; ran on a sandbox copy, printed "added #4"

## List
- what: Show every note's id, title and tags, optionally only those with one tag.
- cli: `list` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `notes.json` @ store.py
- verify: List
- status: traced: ran it (receipt in .features/); not `proven` until Export is fixed, since verify-loop's mutation proof needs the whole suite green; ran `list --tag home`, printed notes #1 and #3

## Search
- what: Find notes whose title or body contains a word (case-insensitive).
- cli: `search` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `notes.json` @ store.py
- verify: Search
- status: traced: ran it (receipt in .features/); not `proven` until Export is fixed, since verify-loop's mutation proof needs the whole suite green; ran `search dune`, printed #3 Books

## Tag
- what: Add a tag to an existing note by id (no duplicates; exit 1 if the id is unknown).
- cli: `tag` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/tag.py > `save` @ store.py > `notes.json` @ store.py
- effect: rewrites notes.json with the tag added
- verify: Tag
- status: traced: ran it (receipt in .features/); not `proven` until Export is fixed, since verify-loop's mutation proof needs the whole suite green; ran on a sandbox copy, printed "tagged #1 urgent"

## Export
- what: Write all notes (id, title, body) to a CSV file for spreadsheets.
- cli: `export` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/export.py > `DictWriter` @ commands/export.py
- effect: writes the CSV at the given path; reads notes.json only
- verify: Export
- status: traced: BROKEN in practice: crashes with ValueError on any note, because each note has `tags` and COLUMNS lacks it (commands/export.py:3); the CSV gets only its header. Failed receipt kept.

## Purge
- what: Delete every note; refuses (exit 1) without `--yes`.
- cli: `purge` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `notes.json` @ store.py
- effect: overwrites notes.json with []
- verify: Purge
- status: traced: read the chain; not run by hand because it deletes (the test runs it on a sandbox copy only)

## Not features
- cli: `debug-dump` @ notes.py: developer dump of raw notes.json, no help text, not a user feature


<!-- file written by the agent: fixture/VERIFY.md -->
# VERIFY

Tests drive the real CLI (`notes.main`) on a temp copy of notes.json; they never touch the real notes.

## Add
- test: `python -m pytest tests/test_cli.py -q -k test_add`
- fail-signal: `FAILED tests/test_cli.py::test_add`
- path: notes.py, commands/add.py, store.py
- oracle: tests/test_cli.py

## List
- test: `python -m pytest tests/test_cli.py -q -k test_list`
- fail-signal: `FAILED tests/test_cli.py::test_list`
- path: notes.py, commands/listing.py, store.py
- oracle: tests/test_cli.py

## Search
- test: `python -m pytest tests/test_cli.py -q -k test_search`
- fail-signal: `FAILED tests/test_cli.py::test_search`
- path: notes.py, commands/search.py, store.py
- oracle: tests/test_cli.py

## Tag
- test: `python -m pytest tests/test_cli.py -q -k test_tag`
- fail-signal: `FAILED tests/test_cli.py::test_tag`
- path: notes.py, commands/tag.py, store.py
- oracle: tests/test_cli.py

## Export
- test: `python -m pytest tests/test_cli.py -q -k test_export`
- fail-signal: `FAILED tests/test_cli.py::test_export`
- path: notes.py, commands/export.py, store.py
- oracle: tests/test_cli.py

## Purge
- test: `python -m pytest tests/test_cli.py -q -k test_purge`
- fail-signal: `FAILED tests/test_cli.py::test_purge`
- path: notes.py, commands/purge.py, store.py
- oracle: tests/test_cli.py

## Blind spots
- debug-dump is not checked (developer-only)
- store.py's real notes.json path is replaced by the sandbox in every check
