`fixture/` now has a feature map, so the next agent session doesn't have to rediscover the CLI. The map's strict check passes with zero problems in every category, and your `notes.json` is byte-for-byte unchanged (I compared it against a backup).

**What I left in the repo**
- **`FEATURES.md`**: the map. It covers the five working commands: `add`, `list`, `search`, `export` and `purge`. For each one it gives what it does for the user, the exact command, the code path from `notes.py` through to `notes.json`, and its check in VERIFY.md.
- **`VERIFY.md` + `tests/`**: one test file per command. The tests run against a temporary notes file, never the real one. Each check was shown to fail when I deliberately broke the command it covers (done in scratch copies), and verify-loop reports green.
- **`tests/sandbox_cli.py`**: runs any command on a throwaway copy of the repo. Use it to try commands that write, so your real notes are never touched.
- **`README.md`**: a new line telling agents to read `FEATURES.md` first and to use the sandbox runner for anything that writes.
- **Generated files**: `.features/` (the saved results of running each command) and `.verify-state*` (verify-loop's records), plus a `.gitignore` for the state files and `__pycache__`.

**Status of each command**
- **`add`, `list`, `search`, `export`:** marked `proven`. I ran each one for real and the run is saved. `add` ran on a sandbox copy and `export` wrote to a temp file, so neither touched your notes.
- **`purge`:** marked `traced`. I read the code all the way through and its test passes on temp data, but I didn't run it on your notes because it deletes everything with no backup.

**A bug I found:** `notes sync` shows up in `--help` as "sync notes with the cloud", but nothing handles it. Running it crashes with `TypeError: 'NoneType' object is not callable`. I listed it under "Not features" with that reason rather than as a feature. The check still watches that line, so it will go stale if `sync` is built or removed. Either implement it or remove it from the parser in `notes.py`.

After any change that adds, renames or removes a command, run `features.py check --strict` (in the feature-map skill's `scripts/` folder) to catch drift.

<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

What the `notes` CLI can do and how each feature is reached. Run everything as
`python notes.py <command>`; dispatch is `HANDLERS` in notes.py. All notes live in `notes.json`
(the owner's real notes): to try a command that writes, use `python tests/sandbox_cli.py <command> ...`,
which runs it on a throwaway copy. Checks are in VERIFY.md; `features.py check` tests this map
against the code.

## Add
- what: Save a new note (title, body, optional repeated `--tag`) with the next free id.
- cli: `add` @ notes.py
- trace: `main` @ notes.py > `HANDLERS` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `PATH` @ store.py
- effect: appends a note to notes.json; prints `added #<id>`
- verify: Add
- status: proven: `python tests/sandbox_cli.py add` exit 0 on a copy; VERIFY Add rejected a mutation

## List
- what: Show every note as `#id title  [tags]`, or only those with `--tag <tag>`.
- cli: `list` @ notes.py
- trace: `main` @ notes.py > `HANDLERS` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `PATH` @ store.py
- verify: List
- status: proven: `python notes.py list` exit 0; VERIFY List rejected a mutation

## Search
- what: Find notes whose title or body contains the query, case-insensitive; prints `#id title`.
- cli: `search` @ notes.py
- trace: `main` @ notes.py > `HANDLERS` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `PATH` @ store.py
- verify: Search
- status: proven: `python notes.py search dune` exit 0; VERIFY Search rejected a mutation

## Export
- what: Write all notes as indented JSON to the file path given.
- cli: `export` @ notes.py
- trace: `main` @ notes.py > `HANDLERS` @ notes.py > `run` @ commands/export.py > `all` @ store.py > `PATH` @ store.py
- effect: creates/overwrites the target file; notes.json is only read
- verify: Export
- status: proven: `python notes.py export <tmp file>` exit 0; VERIFY Export rejected a mutation

## Purge
- what: Delete every note; refuses (exit 1) unless `--yes` is given.
- cli: `purge` @ notes.py
- trace: `main` @ notes.py > `HANDLERS` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `PATH` @ store.py
- needs: `--yes`
- effect: empties notes.json, irreversibly (no backup)
- verify: Purge
- status: traced: read the chain; destructive, so never run on the real notes, only on temp data in tests/test_purge.py

## Not features
- cli: `sync` @ notes.py: listed in `--help` as "sync notes with the cloud" but has no entry in `HANDLERS`; running it crashes with `TypeError: 'NoneType' object is not callable` (exit 1)

## Not built
- Cloud sync (see `sync` above), editing a note, deleting a single note.


<!-- file written by the agent: fixture/VERIFY.md -->
require: challenge

## Add
- path: notes.py, store.py, commands/add.py
- test: `python -m unittest tests/test_add.py`
- oracle: tests/helpers.py
- fail-signal: expected new note #4 saved
- fail-proof: challenge dropped the --tag values in commands/add.py; test_add failed with the signal

## List
- path: notes.py, store.py, commands/listing.py
- test: `python -m unittest tests/test_list.py`
- oracle: tests/helpers.py
- fail-signal: expected only home notes listed
- fail-proof: challenge made the --tag filter always true in commands/listing.py; test_list failed with the signal

## Search
- path: notes.py, store.py, commands/search.py
- test: `python -m unittest tests/test_search.py`
- oracle: tests/helpers.py
- fail-signal: expected body match on Books
- fail-proof: challenge stopped matching the body in commands/search.py; test_search failed with the signal

## Export
- path: notes.py, store.py, commands/export.py
- test: `python -m unittest tests/test_export.py`
- oracle: tests/helpers.py
- fail-signal: expected exported file to equal all notes
- fail-proof: challenge dropped the last note from the export in commands/export.py; test_export failed with the signal

## Purge
- path: notes.py, store.py, commands/purge.py
- test: `python -m unittest tests/test_purge.py`
- oracle: tests/helpers.py
- fail-signal: expected no notes left after purge --yes
- fail-proof: challenge skipped store.save([]) in commands/purge.py; test_purge failed with the signal

## Blind spots
- `tests/sandbox_cli.py` is a manual helper for running writing commands on a copy, not a check.
- `sync` has no handler and crashes; nothing to verify until it is built.
