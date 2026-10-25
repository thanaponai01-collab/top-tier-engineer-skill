I've added a feature map to `fixture/`, and a new session can now learn what the tool does from it without exploring the code. While building it I found that **`export` is broken**: it crashes on every run.

**What's in the repo now**
- **`FEATURES.md`**: one section per command (add, list, search, tag, export, purge). Each says what it does, how to call it, the code path from `notes.py` to `notes.json`, and how I know it works. `debug-dump` is listed under "Not features" because it's a hidden developer command.
- **`VERIFY.md`** and **`tests/check_cli.py`**: one check per command. Each check copies the CLI into a temp folder with sample notes and runs the command there.
- **`CLAUDE.md`**: a short pointer that tells new sessions to read `FEATURES.md` first, and not to run commands that change data against the real `notes.json`.
- **`.features/`**: saved records of each command run. `.verify-state*` is the check tool's state.

**Results**
- The map's own consistency check (`features.py check --strict`) passes with no problems.
- The add, list, search, tag and purge checks pass.
- Your real `notes.json` was never written to; it still holds the same 3 notes.

**The export bug:** `commands/export.py` writes only the columns `id, title, body`, but every note also has `tags`. The CSV writer raises `ValueError: dict contains fields not in fieldnames: 'tags'`, so export crashes on any note. The README describes export as the CSV you open in a spreadsheet, so it's a real bug. I didn't change the code because you didn't ask me to.

**What's still unproven:** every feature is marked "traced" (I read the code and ran the command on a copy), not "proven". "Proven" also needs each check to be seen failing on a deliberately broken copy. The check tool won't run that test while any check fails, so the export bug blocks it for all six features. I also ran purge only on throwaway copies, never on your real notes.

**Decision for you:** should I fix export? Either add `tags` as a column, or tell the writer to skip fields it doesn't list. After that I can run the broken-copy test and upgrade the features to "proven".

<!-- file written by the agent: fixture/CLAUDE.md -->
# notes CLI

Read `FEATURES.md` first: every command, its entry point, its code path and its status. Checks for
each feature are in `VERIFY.md` (`python tests/check_cli.py <command>`, run in a temp copy).
`notes.json` holds the owner's real notes: never run add/tag/purge/export against it; use a copy.


<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

What the `notes` CLI does and how each feature is reached. Every command is
`python notes.py <command>`, dispatched by `HANDLERS` in notes.py to `run(store, args)` in
`commands/`. All state is `notes.json` (via store.py, path fixed next to store.py). That file holds
the owner's real notes: to try a writing command, copy the repo to a temp dir and run it there.
`python <feature-map>/scripts/features.py check` tests every line here against the code.

## Add
- what: Save a new note with a title, a body and optional tags; prints its new id.
- cli: `add` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `PATH` @ store.py
- effect: appends `{"id", "title", "body", "tags"}` to notes.json; id = max id + 1
- verify: Add
- status: traced: read the chain; ran `add T B --tag x` on a copy, printed `added #4`

## List
- what: Print every note as `#id title  [tags]`, or only those carrying `--tag NAME`.
- cli: `list` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `PATH` @ store.py
- verify: List
- status: traced: read the chain; ran `list --tag x` on a copy, printed the tagged note

## Search
- what: Print notes whose title or body contains the query, case-insensitive.
- cli: `search` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `PATH` @ store.py
- verify: Search
- status: traced: read the chain; ran `search dune` on a copy, printed `#3 Books`

## Tag
- what: Add a tag to the note with a given id (no duplicate); exit 1 if the id does not exist.
- cli: `tag` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/tag.py > `save` @ store.py > `PATH` @ store.py
- effect: rewrites notes.json with the tag appended
- verify: Tag
- status: traced: read the chain; ran `tag 1 zz` on a copy, printed `tagged #1 zz`

## Export
- what: Write all notes to a CSV (columns id, title, body) for a spreadsheet.
- cli: `export` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/export.py > `COLUMNS` @ commands/export.py > `DictWriter` @ commands/export.py
- effect: creates the file at the given path
- verify: Export
- status: traced: BROKEN in use. `export out.csv` crashes (ValueError: dict contains fields not in fieldnames: 'tags') on any note, since every note has `tags` and COLUMNS omits it. Failed receipt in .features/export.json.

## Purge
- what: Delete ALL notes (empties notes.json); refuses and exits 1 without `--yes`.
- cli: `purge` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `PATH` @ store.py
- effect: notes.json becomes `[]`; irreversible
- verify: Purge
- status: traced: read the chain; only the refusal (no `--yes`) was run, on a copy. Destructive, never run against the real notes.json

## Not features
- cli: `debug-dump` @ notes.py: developer command, no help text so hidden from `--help`; prints raw notes.json


<!-- file written by the agent: fixture/VERIFY.md -->
# VERIFY

Each check runs one `notes` command in a temp copy of the CLI with seeded notes
(`tests/check_cli.py`); the real notes.json is never touched. Expected results come from the
README and `python notes.py --help`.

## Add
- path: notes.py, store.py, commands/add.py
- test: `python tests/check_cli.py add`
- oracle: README.md, tests/check_cli.py
- fail-signal: FAIL: expected 'added #4'

## List
- path: notes.py, store.py, commands/listing.py
- test: `python tests/check_cli.py list`
- oracle: README.md, tests/check_cli.py
- fail-signal: FAIL: expected home notes #1 and #3

## Search
- path: notes.py, store.py, commands/search.py
- test: `python tests/check_cli.py search`
- oracle: README.md, tests/check_cli.py
- fail-signal: FAIL: expected '#3 Books'

## Tag
- path: notes.py, store.py, commands/tag.py
- test: `python tests/check_cli.py tag`
- oracle: README.md, tests/check_cli.py
- fail-signal: FAIL: expected #2 tagged urgent

## Export
- path: notes.py, store.py, commands/export.py
- test: `python tests/check_cli.py export`
- oracle: README.md, tests/check_cli.py
- fail-signal: FAIL: expected export to succeed

## Purge
- path: notes.py, store.py, commands/purge.py
- test: `python tests/check_cli.py purge`
- oracle: README.md, tests/check_cli.py
- fail-signal: FAIL: expected no notes after purge --yes

## Blind spots
- `debug-dump` (commands/debug.py): developer-only, hidden from --help; prints notes.json as-is, no check
- every check runs on seeded temp copies; behaviour on a missing or corrupt notes.json is not exercised
